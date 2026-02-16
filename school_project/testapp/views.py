from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Test, Question, TestAttempt, StudentAnswer, Answer, EnrollmentTest, AnswerSelection
from .serializers import (
    TestSerializer, QuestionSerializer,TestAttemptResultSerializer,TestSerializer,
    TestAttemptSerializer, AnswerSerializer, StudentAnswerSerializer,EnrollmentTestSerializer
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
from schoolapp.models import Enrollment, Course
from django.shortcuts import render, get_object_or_404, redirect
from .models import Test, Question, Answer
from .forms import TestForm, QuestionForm, AnswerForm
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from random import sample
from collections import defaultdict


def get_teacher_profile_or_403(user):
    if not getattr(user, "is_authenticated", False):
        raise PermissionDenied("Authentication credentials were not provided.")

    if not hasattr(user, "teacher_profile"):
        raise PermissionDenied("Only teacher users can access this endpoint.")

    return user.teacher_profile






# STEP 1: Create and manage Tests
class TestViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Test.objects.all()
    serializer_class = TestSerializer

    def get_queryset(self):
        teacher = get_teacher_profile_or_403(self.request.user)
        return Test.objects.filter(teacher=teacher)

    def perform_create(self, serializer):
        teacher = get_teacher_profile_or_403(self.request.user)
        serializer.save(teacher=teacher)

    def retrieve(self, request, *args, **kwargs):
        test = self.get_object()
        teacher = get_teacher_profile_or_403(request.user)
        if test.teacher != teacher:
            raise PermissionDenied("Siz bu testni ko‘ra olmaysiz.")
        return super().retrieve(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        test = self.get_object()
        teacher = get_teacher_profile_or_403(request.user)
        if test.teacher != teacher:
            raise PermissionDenied("Siz bu testni o‘zgartira olmaysiz.")
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        test = self.get_object()
        teacher = get_teacher_profile_or_403(request.user)
        if test.teacher != teacher:
            raise PermissionDenied("Siz bu testni o‘chira olmaysiz.")
        return super().destroy(request, *args, **kwargs)


# STEP 2: Create and manage Questions
class QuestionViewSet(viewsets.ModelViewSet):
    serializer_class = QuestionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        teacher = get_teacher_profile_or_403(self.request.user)
        queryset = Question.objects.filter(test__teacher=teacher)
        
        # Agar query parametrlarda test id berilgan bo'lsa, filter qilamiz
        test_id = self.request.query_params.get('test')
        if test_id:
            queryset = queryset.filter(test_id=test_id)

        return queryset

    def perform_create(self, serializer):
        teacher = get_teacher_profile_or_403(self.request.user)
        test_id = self.request.data.get('test')
        test = get_object_or_404(Test, id=test_id, teacher=teacher)
        serializer.save(test=test)

    def perform_update(self, serializer):
        teacher = get_teacher_profile_or_403(self.request.user)
        test_id = self.request.data.get('test')
        test = get_object_or_404(Test, id=test_id, teacher=teacher)
        serializer.save(test=test)


# STEP 3: Create and manage Answers
class AnswerViewSet(viewsets.ModelViewSet):
    serializer_class = AnswerSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        teacher = get_teacher_profile_or_403(self.request.user)
        queryset = Answer.objects.filter(
            question__test__teacher=teacher
        )

        # Agar query parametrlarda question id berilgan bo'lsa, filter qilamiz
        question_id = self.request.query_params.get('question')
        if question_id:
            queryset = queryset.filter(question_id=question_id)

        return queryset

    def perform_create(self, serializer):
        teacher = get_teacher_profile_or_403(self.request.user)
        question_id = self.request.data.get('question')
        question = get_object_or_404(
            Question,
            id=question_id,
            test__teacher=teacher
        )
        serializer.save(question=question)

    def perform_update(self, serializer):
        teacher = get_teacher_profile_or_403(self.request.user)
        question_id = self.request.data.get('question')
        question = get_object_or_404(
            Question,
            id=question_id,
            test__teacher=teacher
        )
        serializer.save(question=question)





# Student gets assigned N random tests
class StudentAssignedTestsView(APIView):
    # permission_classes = [IsAuthenticated, IsStudent]

    def get(self, request):
        student = request.user.student_profile
        # Studentning barcha enrollments larini olamiz
        enrollments = Enrollment.objects.filter(student=student)

        # Shu enrollments ga tegishli enrollment testlarni olamiz
        enrollment_tests = EnrollmentTest.objects.filter(course__in=enrollments)
        
        # Testlarni olish (yoki EnrollmentTest-da `test` ForeignKey bor)
        tests = Test.objects.filter(id__in=enrollment_tests.values_list('test_id', flat=True))

        attempts = []
        for test in tests:
            attempt, created = TestAttempt.objects.get_or_create(student=student, test=test)
            attempts.append(attempt)

        serializer = TestAttemptSerializer(attempts, many=True)
        return Response(serializer.data)


# Student submits answers
class SubmitAnswersView(APIView):
    # permission_classes = [IsAuthenticated, IsStudent]

    def post(self, request, attempt_id):
        attempt = get_object_or_404(TestAttempt, id=attempt_id, student=request.user.student_profile)
        answers_data = request.data.get('answers', [])

        total_score = 0.0

        for ans in answers_data:
            question = get_object_or_404(Question, id=ans['question_id'])
            selected_options = ans.get('selected_option', [])

            student_answer = StudentAnswer.objects.create(
                attempt=attempt,
                question=question
            )

            # Single choice variantini listga aylantirish
            if not isinstance(selected_options, list):
                selected_options = [selected_options]

            scored_mark = 0.0
            for opt_id in selected_options:
                answer_obj = get_object_or_404(Answer, id=opt_id)
                student_answer.selected_answers.add(answer_obj)
                if answer_obj.is_correct:
                    scored_mark += answer_obj.question.mark

            student_answer.scored_mark = scored_mark
            student_answer.save()

            total_score += scored_mark

        attempt.total_score = total_score
        attempt.submitted_at = timezone.now()
        attempt.save()

        return Response({"total_score": total_score}, status=status.HTTP_200_OK)


class StudentTestResultView(APIView):
    #permission_classes = [IsAuthenticated, IsStudent]

    def get(self, request, test_id):
        student = request.user.student_profile
        attempt = TestAttempt.objects.filter(test_id=test_id, student=student).first()
        if not attempt:
            return Response({'detail': 'Test topilmadi yoki yechilmagan.'}, status=404)

        serializer = TestAttemptResultSerializer(attempt)
        return Response(serializer.data)

class TeacherTestResultsView(APIView):
    # #permission_classes = [IsAuthenticated, IsTeacher]

    def get(self, request, test_id):
        teacher = get_teacher_profile_or_403(request.user)
        test = get_object_or_404(Test, id=test_id, teacher=teacher)
        attempts = TestAttempt.objects.filter(test=test).select_related('student')
        serializer = TestAttemptResultSerializer(attempts, many=True)
        return Response(serializer.data)






def test_results_view(request, test_id):
    test = get_object_or_404(Test, id=test_id)
    total_questions = test.questions.count()

    attempts = (
        TestAttempt.objects
        .filter(test=test)
        .annotate(
            correct_count=Count(
                'selections',
                filter=Q(selections__selected_answer__is_correct=True)
            )
        )
        .select_related('student')
    )

    # Kontekstga total_questions ni qo'shish
    return render(request, 'teacher_test_results.html', {
        'test': test,
        'attempts': attempts,
        'total_questions': total_questions,
    })



def attempt_detail_view(request, attempt_id):
    attempt = get_object_or_404(TestAttempt, id=attempt_id)
    selections = attempt.selections.select_related('question', 'selected_answer')

    return render(request, 'attempt_detail.html', {
        'attempt': attempt,
        'selections': selections
    })



def student_test_attempts_view(request):
    student = Student.objects.get(user=request.user)
    attempts = TestAttempt.objects.filter(student=student).select_related('test')
    return render(request, 'student_attempts.html', {'attempts': attempts})



class EnrollmentTestViewSet(viewsets.ModelViewSet):
    serializer_class = EnrollmentTestSerializer
    permission_classes = [permissions.IsAuthenticated, IsTeacher]

    def get_queryset(self):
        teacher = get_teacher_profile_or_403(self.request.user)
        return EnrollmentTest.objects.filter(teacher=teacher)

    def perform_create(self, serializer):
        teacher = get_teacher_profile_or_403(self.request.user)
        course_id = self.request.data.get('course')

        try:
            course = Course.objects.get(id=course_id, teacher=teacher)
        except Course.DoesNotExist:
            raise PermissionDenied("Siz bu kursni boshqara olmaysiz.")

        serializer.save(teacher=teacher, course=course)

    def perform_update(self, serializer):
        teacher = get_teacher_profile_or_403(self.request.user)
        course_id = self.request.data.get('course')

        if course_id:
            try:
                course = Course.objects.get(id=course_id, teacher=teacher)
            except Course.DoesNotExist:
                raise PermissionDenied("Siz bu kursni boshqara olmaysiz.")
            serializer.save(course=course)
        else:
            serializer.save()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        teacher = get_teacher_profile_or_403(request.user)
        if instance.teacher != teacher:
            raise PermissionDenied("Siz bu enrollment testni o'chira olmaysiz.")
        return super().destroy(request, *args, **kwargs)

# views.py
def student_test_detail_view(request, test_id):
    test = get_object_or_404(Test, id=test_id)
    all_questions = list(test.questions.all())
    selected_questions = random.sample(all_questions, min(len(all_questions), 10))
    return render(request, 'student_test_detail.html', {
        'test': test,
        'questions': selected_questions,
    })






def student_tests_view(request):
    student = request.user.student_profile

    # 1) studentning enrollments -> kurslar
    enrollments = Enrollment.objects.filter(student=student)
    courses = [e.course for e in enrollments]

    # 2) shu kurslarga tayinlangan EnrollmentTestlarni olish
    enrollment_tests = (
        EnrollmentTest.objects
        .filter(course__in=courses)
        .select_related('test', 'teacher', 'course')
        .prefetch_related('test__questions')
    )

    # 3) test listi (for lookup)
    tests = [et.test for et in enrollment_tests]

    # 4) har bir test uchun oxirgi (latest) attempt (student bo'yicha)
    attempts_qs = TestAttempt.objects.filter(student=student, test__in=tests).order_by('test_id', '-started_at')
    attempts_by_test = {}
    for att in attempts_qs:
        # agar avvalgi att qo'yilmagan bo'lsa, eng yangi ni saqlaymiz
        if att.test_id not in attempts_by_test:
            attempts_by_test[att.test_id] = att

    # 5) har bir test bo'yicha qancha urinish qilingan (student uchun)
    attempt_counts = (
        TestAttempt.objects
        .filter(student=student, test__in=tests)
        .values('test')
        .annotate(count=Count('id'))
    )
    attempts_count_map = { item['test']: item['count'] for item in attempt_counts }

    # 6) nechta urinish qolgan (enrollment_test.attempt_count - used)
    remaining_map = {}
    for et in enrollment_tests:
        used = attempts_count_map.get(et.test_id, 0)
        remaining_map[et.test_id] = max(et.attempt_count - used, 0)

    now = timezone.now()

    context = {
        'enrollment_tests': enrollment_tests,        # enrollments with test/course/teacher
        'attempts_by_test': attempts_by_test,       # latest attempt per test (or missing)
        'attempts_count_map': attempts_count_map,   # used attempts count per test
        'remaining_map': remaining_map,             # remaining attempts per test
        'now': now,
    }
    return render(request, 'student_test.html', context)




from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def submit_test_view(request, test_id):
    test = get_object_or_404(Test, id=test_id)
    student = request.user.student_profile

    # Get only the questions answered (those submitted)
    question_ids = [int(key.split('_')[1]) for key in request.POST if key.startswith('question_')]
    questions = Question.objects.filter(id__in=question_ids)

    attempt = TestAttempt.objects.create(student=student, test=test)

    score = 0
    for question in questions:
        selected_id = request.POST.get(f'question_{question.id}')
        selected_answer = None
        if selected_id:
            selected_answer = Answer.objects.get(id=selected_id)
            AnswerSelection.objects.create(
                attempt=attempt,
                question=question,
                selected_answer=selected_answer
            )
            if selected_answer.is_correct:
                score += question.mark
        else:
            AnswerSelection.objects.create(
                attempt=attempt,
                question=question
            )

    total_mark = sum(q.mark for q in questions)
    attempt.score = round(score, 2)
    attempt.percentage = round((score / total_mark) * 100 if total_mark else 0, 2)
    attempt.completed_at = timezone.now()
    attempt.save()

    correct_count = AnswerSelection.objects.filter(attempt=attempt, selected_answer__is_correct=True).count()

    return render(request, 'test_submitted.html', {
        'test': test,
        'score': attempt.score,
        'percentage': attempt.percentage,
        'total_questions': questions.count(),
        'correct_answers': correct_count,
    })




class TeacherTestHTMLView(TemplateView):
    template_name = "teacher_tests.html"



def teacher_tests(request):
    tests = Test.objects.filter(teacher=request.user.teacher_profile)
    
    if request.method == 'POST':
        form = TestForm(request.POST)
        if form.is_valid():
            form.instance.teacher = request.user.teacher_profile
            form.save()
            return redirect('teacher_tests')
    else:
        form = TestForm()

    return render(request, 'teacher_tests.html', {'tests': tests, 'form': form})


def teacher_questions(request, test_id):
    test = get_object_or_404(Test, id=test_id, teacher=request.user.teacher_profile)
    questions = Question.objects.filter(test=test)

    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            form.instance.test = test
            form.save()
            return redirect('teacher_questions', test_id=test.id)
    else:
        form = QuestionForm()

    return render(request, 'teacher_questions.html', {'test': test, 'questions': questions, 'form': form})


def teacher_answers(request, question_id):
    question = get_object_or_404(Question, id=question_id, test__teacher=request.user.teacher_profile)
    answers = Answer.objects.filter(question=question)

    if request.method == 'POST':
        form = AnswerForm(request.POST)
        if form.is_valid():
            form.instance.question = question
            form.save()
            return redirect('teacher_answers', question_id=question.id)
    else:
        form = AnswerForm()

    return render(request, 'teacher_answers.html', {'question': question, 'answers': answers, 'form': form})


def test_list(request):
    tests = Test.objects.filter(teacher=request.user.teacher_profile)
    return render(request, 'tests/test_list.html', {'tests': tests})

def test_create(request):
    if request.method == 'POST':
        form = TestForm(request.POST)
        if form.is_valid():
            form.instance.teacher = request.user.teacher_profile
            form.save()
            return redirect('test-list')
    else:
        form = TestForm()
    return render(request, 'tests/test_form.html', {'form': form, 'form_title': 'Yangi test qo‘shish'})

def test_edit(request, pk):
    test = get_object_or_404(Test, pk=pk, teacher=request.user.teacher_profile)
    if request.method == 'POST':
        form = TestForm(request.POST, instance=test)
        if form.is_valid():
            form.save()
            return redirect('test-list')
    else:
        form = TestForm(instance=test)
    return render(request, 'tests/test_form.html', {'form': form, 'form_title': 'Testni tahrirlash'})

def test_delete(request, pk):
    test = get_object_or_404(Test, pk=pk, teacher=request.user.teacher_profile)
    if request.method == 'POST':
        test.delete()
        return redirect('test-list')
    return render(request, 'tests/test_confirm_delete.html', {'test': test})




def teacher_panel(request):
    return render(request, 'teacher_panel.html')
