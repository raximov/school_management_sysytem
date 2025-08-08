from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Test, Question, TestAttempt, StudentAnswer, Answer, CourseTest
from .serializers import (
    TestSerializer, QuestionSerializer,TestAttemptResultSerializer,TestSerializer,
    TestAttemptSerializer, StudentAnswerSerializer
)
from schoolapp.permissions import IsTeacher, IsStudent
from schoolapp.models import Student
import random
from django.utils import timezone
from django.shortcuts import get_object_or_404, render
import random
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, ListView

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, NotFound
from django.http import HttpResponse



class TestViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsTeacher]

    def get_queryset(self):
        return Test.objects.filter(teacherid=self.request.user.teacher_profile)

    def get_serializer_class(self):
        if self.action == 'create':
            return TestSerializer
        return TestSerializer

    def perform_create(self, serializer):
        serializer.save(teacherid=self.request.user.teacher_profile)

    def retrieve(self, request, *args, **kwargs):
        test = self.get_object()
        if test.teacherid != request.user.teacher_profile:
            raise PermissionDenied("Siz bu testni ko‘ra olmaysiz.")
        serializer = self.get_serializer(test)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        test = self.get_object()
        if test.teacherid != request.user.teacher_profile:
            raise PermissionDenied("Siz bu testni o‘zgartira olmaysiz.")
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        test = self.get_object()
        if test.teacherid != request.user.teacher_profile:
            raise PermissionDenied("Siz bu testni o‘chira olmaysiz.")
        return super().destroy(request, *args, **kwargs)

class TeacherTestHTMLView(LoginRequiredMixin, ListView):
    model = Test
    template_name = 'teacher_test_list.html'
    context_object_name = 'tests'

    def get_queryset(self):
        user = self.request.user
        return Test.objects.filter(teacherid=user.teacher_profile)

# Student gets assigned N random tests
class StudentAssignedTestsView(APIView):
    permission_classes = [IsAuthenticated, IsStudent]

    def get(self, request):
        student = request.user.student_profile
        test_count = 2  # Adjust this number to how many tests each student should get

        # If not already assigned
        if not TestAttempt.objects.filter(studentid=student).exists():
            all_tests = list(Test.objects.all())
            selected_tests = random.sample(all_tests, min(test_count, len(all_tests)))

            # Create attempt records
            for test in selected_tests:
                TestAttempt.objects.create(studentid=student, testid=test)

        attempts = TestAttempt.objects.filter(studentid=student)
        serializer = TestAttemptSerializer(attempts, many=True)
        
        return Response(serializer.data)

# Student submits answers
class SubmitAnswersView(APIView):
    permission_classes = [IsAuthenticated, IsStudent]

    def post(self, request, attempt_id):
        attempt = TestAttempt.objects.get(id=attempt_id, student=request.user.student_profile)
        answers_data = request.data.get('answers', [])

        for ans in answers_data:
            StudentAnswer.objects.create(
                attempt=attempt,
                question_id=ans['question_id'],
                selected_option_id=ans.get('selected_option'),
                written_answer=ans.get('written_answer', '')
            )

        attempt.submitted_at = timezone.now()
        attempt.save()
        return Response({"detail": "Answers submitted"}, status=status.HTTP_200_OK)

class StudentTestResultView(APIView):
    permission_classes = [IsAuthenticated, IsStudent]

    def get(self, request, test_id):
        student = request.user.student_profile
        attempt = TestAttempt.objects.filter(test_id=test_id, student=student).first()
        if not attempt:
            return Response({'detail': 'Test topilmadi yoki yechilmagan.'}, status=404)

        serializer = TestAttemptResultSerializer(attempt)
        return Response(serializer.data)

class TeacherTestResultsView(APIView):
    permission_classes = [IsAuthenticated, IsTeacher]

    def get(self, request, test_id):
        teacher = request.user.teacher_profile
        test = get_object_or_404(Test, id=test_id, creator=teacher)
        attempts = TestAttempt.objects.filter(test=test)
        serializer = TestAttemptResultSerializer(attempts, many=True)
        return Response(serializer.data)

def student_random_test_view(request):
    # Just taking the first test as example; you may replace it with random logic
    test = Test.objects.prefetch_related('questions__answer_options').first()
    return render(request, 'student_test.html', {'test': test})


   


def submit_test_view(request):
    try:
        coursetest = CourseTest.objects.get(testid_id=test_id, courseid__students=student)
    except CourseTest.DoesNotExist:
        return HttpResponse("Sizga bu test topshirishga ruxsat berilmagan.", status=403)
    attempts = TestAttempt.objects.filter(studentid=student, testid_id=test_id).count()
    if attempts >= coursetest.attemt_count:
        return HttpResponse("Siz testni topshirish uchun ruxsat etilgan urinishlar sonini tugatdingiz.", status=403)

    if request.method == 'POST':
        test_id = request.POST.get('test_id')

        # ⚠️ Foydalanuvchini olish (request.user orqali)
        student = Student.objects.get(user=request.user)

        # 1. TestAttempt yaratish
        attempt = TestAttempt.objects.create(
            studentid=student,
            testid_id=test_id,
            completed_at=timezone.now()
        )

        total_score = 0.0
        correct_count = 0
        total_questions = 0

        for key, value in request.POST.items():
            if key.startswith('question_'):
                question_id = key.split('_')[1]
                question = Question.objects.get(id=question_id)

                if question.question_type == 'OC':
                    selected_answer_ids = [value]  # single choice, one value
                elif question.question_type == 'MC':
                    selected_answer_ids = request.POST.getlist(key)  # list of values
                else:
                    continue  # other types not handled yet

                # Create StudentAnswer
                student_answer = StudentAnswer.objects.create(
                    attempt=attempt,
                    questionid=question
                )

                scored_mark = 0.0
                for ans_id in selected_answer_ids:
                    try:
                        answer = Answer.objects.get(id=ans_id)
                        student_answer.selected_answers.add(answer)
                        if answer.is_correct:
                            scored_mark += answer.mark
                    except Answer.DoesNotExist:
                        pass

                student_answer.scored_mark = scored_mark
                student_answer.save()

                total_score += scored_mark
                total_questions += 1
                if scored_mark > 0:
                    correct_count += 1


        context = {
            'total_score': round(total_score, 2),
            'correct_count': correct_count,
            'total_questions': total_questions,
        }
        return render(request, 'test_result.html', context)

    return HttpResponse("Invalid request method", status=400)


def student_test_attempts_view(request):
    student = Student.objects.get(user=request.user)
    attempts = TestAttempt.objects.filter(studentid=student).select_related('testid')
    return render(request, 'student_attempts.html', {'attempts': attempts})
