from rest_framework import viewsets
from rest_framework.generics import RetrieveUpdateDestroyAPIView, ListCreateAPIView
from .models import Department, Classroom, Teacher, Student, Course, Enrollment, Task, TaskSubmission
from .serializers import (
    DepartmentSerializer, ClassroomSerializer,
    TeacherSerializer, StudentSerializer,
    CourseSerializer, EnrollmentSerializer, TaskSerializer, StudentSubmissionSerializer, TeacherSubmissionSerializer, StudentTaskStatsSerializer, 
)
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView, LogoutView

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from .forms import StudentRegisterForm  # Make sure this exists
from rest_framework.decorators import api_view
from django.shortcuts import get_object_or_404
from .permissions import IsStudent, IsTeacher, IsAuthenticated
from django.db.models import Count, Q, F, FloatField, ExpressionWrapper,Avg
from collections import defaultdict
from django.db.models import OuterRef, Subquery
from django.db.models.functions import Coalesce
from django.urls import reverse_lazy
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET
import json


class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer


class ClassroomViewSet(viewsets.ModelViewSet):
    queryset = Classroom.objects.all()
    serializer_class = ClassroomSerializer


class TeacherViewSet(viewsets.ModelViewSet):
    queryset = Teacher.objects.all()
    serializer_class = TeacherSerializer


class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer


from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

@method_decorator(csrf_exempt, name='dispatch')  # testing / HTML forms uchun
class EnrollmentViewSet(viewsets.ModelViewSet):
    queryset = Enrollment.objects.all()
    serializer_class = EnrollmentSerializer
    permission_classes = [IsAuthenticated]
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = 'enrollment_list.html'

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if request.accepted_renderer.format == 'html':
            return Response({'enrollments': queryset}, template_name=self.template_name)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def dispatch(self, request, *args, **kwargs):
        """HTML formdan kelgan _method ni HTTP methodga aylantirish"""
        if "_method" in request.POST:
            method = request.POST["_method"].lower()
            if method == "delete":
                request.method = "DELETE"
            elif method == "put":
                request.method = "PUT"
        return super().dispatch(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save()

    def perform_update(self, serializer):
        serializer.save()

    def create(self, request, *args, **kwargs):
        resp = super().create(request, *args, **kwargs)
        if request.accepted_renderer.format == 'html':
            return redirect('enrollment-list')
        return resp

    def update(self, request, *args, **kwargs):
        resp = super().update(request, *args, **kwargs)
        if request.accepted_renderer.format == 'html':
            return redirect('enrollment-list')
        return resp

    def destroy(self, request, *args, **kwargs):
        resp = super().destroy(request, *args, **kwargs)
        if request.accepted_renderer.format == 'html':
            return redirect('enrollment-list')
        return resp



def register_student(request):
    if request.method == 'POST':
        form = StudentRegisterForm(request.POST, request.FILES)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            if User.objects.filter(username=username).exists():
                form.add_error('username', 'This username is already taken.')
            else:
                user = User.objects.create_user(username=username, password=password)
                student = form.save(commit=False)
                student.user = user
                student.save()
                login(request, user)
                return redirect('student_dashboard')
    else:
        form = StudentRegisterForm()
    return render(request, 'accounts/register_student.html', {'form': form})


def register_teacher(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.email = request.POST.get('email', '')
            user.save()
            # Always create a Teacher profile after registration
            Teacher.objects.create(
                user=user,
                name=request.POST.get('name', ''),
                middle_name=request.POST.get('middle_name', ''),
                last_name=request.POST.get('last_name', ''),
                email=user.email,
                specialization=request.POST.get('specialization', ''),
            )
            login(request, user)
            return redirect('teacher_dashboard')
    else:
        form = UserCreationForm()
    return render(request, 'accounts/register_teacher.html', {'form': form})

class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'

    def get_success_url(self):
        user = self.request.user
        if hasattr(user, 'student'):
            return reverse_lazy('dashboard')
        elif hasattr(user, 'teacher'):
            return reverse_lazy('dashboard')
        return reverse_lazy('dashboard')

class CustomLogoutView(LogoutView):
    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)

@login_required
def post_login_redirect(request):
    if hasattr(request.user, 'student_profile'):
        return redirect('student_dashboard')
    elif hasattr(request.user, 'teacher_profile'):
        return redirect('teacher_dashboard')
    return render(request, 'home.html')

@login_required
@api_view(['GET'])
def student_dashboard(request):
    if not hasattr(request.user, 'student_profile'):
        return HttpResponseForbidden("You are not authorized to view this page.")
     
    student = Student.objects.filter(user=request.user).first()
 
    return render(request, 'accounts/student_dashboard.html', {'student': student})

@login_required
@api_view(['GET'])
def teacher_dashboard(request):
    if not hasattr(request.user, 'teacher_profile'):
        raise request.user.objects.filter(user=request.user).first()
    teacher = Teacher.objects.filter(user=request.user).first()
    return render(request, 'accounts/teacher_dashboard.html', {'teacher': teacher})

@login_required
def dashboard_redirect(request):
    if hasattr(request.user, 'student_profile'):
        return redirect('student_dashboard')
    elif hasattr(request.user, 'teacher_profile'):
        return redirect('teacher_dashboard')
    return render(request, 'home.html')

class MyProtectedView(APIView):
    permission_classes = [IsAuthenticated]
    """
    A protected view that requires authentication.
    """
    def get(self, request):
        return Response({"message": "This is a protected view."}, status=status.HTTP_200_OK)

class MyPublicView(APIView):
    permission_classes = [AllowAny]
    """
    A public view that does not require authentication.
    """
    def get(self, request):
        return Response({"message": "This is a public view."}, status=status.HTTP_200_OK)

# The HTML form and JavaScript code have been removed from this Python file.
# Please place your form and script in a Django template (e.g., templates/accounts/register_student.html).

class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

class StudentTasksListView(APIView):
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = 'student_tasks.html'


    permission_classes = [IsAuthenticated, IsStudent]
    serializer_class = TaskSerializer

    def get(self, request, *args, **kwargs):
        student = request.user.student_profile

        # Studentning barcha kurslari
        course_ids = student.enrollments.values_list('course_id', flat=True)

        # Faqat shu kurslarga tegishli topshiriqlar
        course_tasks = Task.objects.filter(course_id__in=course_ids)

        serializer = self.serializer_class(course_tasks, many=True)

        # Agar foydalanuvchi HTML so‘rasa (Accept: text/html)
        if request.accepted_renderer.format == 'html':
            return Response({'tasks': serializer.data}, template_name=self.template_name)

        # Aks holda JSON qaytadi
        return Response(serializer.data)


class StudentTasksView(APIView):
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = 'student_task_detail.html'
    permission_classes = [IsAuthenticated, IsStudent]
    serializer_class = TaskSerializer

    def get(self, request, pk=None, *args, **kwargs):
        student = request.user.student_profile
        course_ids = student.enrollments.values_list('course_id', flat=True)
        course_tasks = Task.objects.filter(course_id__in=course_ids)

        if pk:
            task = course_tasks.filter(id=pk).first()
            if not task:
                if request.accepted_renderer.format == 'html':
                    return Response({'error': "Task not found"}, template_name='error.html', status=404)
                return Response({"detail": "Task not found or not assigned to this student."}, status=404)
            serializer = self.serializer_class(task)
            if request.accepted_renderer.format == 'html':
                return Response({'task': serializer.data}, template_name=self.template_name)
            return Response(serializer.data)
        else:
            serializer = self.serializer_class(course_tasks, many=True)
            if request.accepted_renderer.format == 'html':
                return Response({'tasks': serializer.data}, template_name='student_tasks.html')
            return Response(serializer.data)




class CourseTasksView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, course_id):
        course = get_object_or_404(course, id=course_id)
        tasks = course.tasks.all()
        serializer = TaskSerializer(tasks, many=True)
        return Response(serializer.data)
    


class SubmitTaskView(APIView):
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = 'submit_task.html'
    permission_classes = [IsAuthenticated, IsStudent]
    serializer_class = StudentSubmissionSerializer

    def get(self, request, pk=None, *args, **kwargs):
        student = request.user.student_profile
        if pk is not None:
            submissions = TaskSubmission.objects.filter(task_id=pk, student=student)
        else:
            submissions = TaskSubmission.objects.filter(student=student)

        serializer = self.serializer_class(submissions, many=True)

        if request.accepted_renderer.format == 'html':
            return Response({'submissions': serializer.data}, template_name=self.template_name)
        return Response(serializer.data)

    def post(self, request, pk):
        if not hasattr(request.user, 'student_profile'):
            return Response({"error": "User has no student profile."}, status=400)

        student = request.user.student_profile
        task = get_object_or_404(Task, id=pk)

        if not student.enrollments.filter(course=task.course).exists():
            return Response({"error": "You are not allowed to submit this task."}, status=403)

        submission, created = TaskSubmission.objects.get_or_create(
            task=task,
            student=student,
            defaults={'teacher': task.teacher, 'student': student}
        )

        submission.submitted_text = request.data.get("submitted_text", "")
        if 'submitted_file' in request.FILES:
            submission.submitted_file = request.FILES['submitted_file']
        submission.is_done = True
        submission.save()

        if request.accepted_renderer.format == 'html':
            return Response({'message': "Task submitted successfully."}, template_name='submit_success.html')

        return Response({"message": "Task submitted successfully."})

class TeacherTaskViewSet(viewsets.ModelViewSet):
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = 'teacher_tasks.html'
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated, IsTeacher]

    def get_queryset(self):
        queryset = Task.objects.filter(teacher__user=self.request.user)
        pk = self.kwargs.get('pk')
        if pk:
            return queryset.filter(pk=pk)
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        if request.accepted_renderer.format == 'html':
            return Response({'tasks': serializer.data}, template_name=self.template_name)
        return Response(serializer.data)


# Teacher Submissions List + Create
class TeacherSubmitListCreateView(ListCreateAPIView):
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = 'teacher_submissions.html'
    serializer_class = TeacherSubmissionSerializer
    permission_classes = [IsAuthenticated, IsTeacher]

    def get_queryset(self):
        return TaskSubmission.objects.filter(task__teacher__user=self.request.user)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        if request.accepted_renderer.format == 'html':
            return Response({'submissions': serializer.data}, template_name=self.template_name)
        return Response(serializer.data)


# Teacher Submission Detail / Update / Delete
class TeacherSubmitRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = 'teacher_submission_detail.html'
    serializer_class = TeacherSubmissionSerializer
    permission_classes = [IsAuthenticated, IsTeacher]

    def get_queryset(self):
        return TaskSubmission.objects.filter(task__teacher__user=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)

        if request.accepted_renderer.format == 'html':
            return Response({'submission': serializer.data}, template_name=self.template_name)
        return Response(serializer.data)




# class TeacherSubmitView(viewsets.ModelViewSet):
#     serializer_class = TeacherSubmissionSerializer
#     permission_classes = [IsAuthenticated, IsTeacher]

#     def get_queryset(self):
#         id = self.kwargs['pk']
#         request = self.request
#         if id:
#             return TaskSubmission.objects.filter(id=id)
#         return TaskSubmission.objects.all()

#     def retrieve(self, request, *args, **kwargs):
#         submission = self.get_object()
#         serializer = self.get_serializer(submission)
#         return Response(serializer.data)

#     def update(self, request, *args, **kwargs):
#         submission = self.get_object()
#         serializer = self.get_serializer(submission, data=request.data, partial=True)
#         serializer.is_valid(raise_exception=True)
#         serializer.save()
#         return Response(serializer.data)


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from django.shortcuts import get_object_or_404
from django.db.models import Avg
from rest_framework.permissions import IsAuthenticated

class TaskStatsTableView(APIView):
    permission_classes = [IsAuthenticated, IsTeacher]
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = 'teacher/task_stats_table.html'

    def get(self, request, pk):
        teacher = request.user.teacher_profile
        task = get_object_or_404(Task, pk=pk, teacher=teacher)

        submissions = TaskSubmission.objects.filter(task=task).select_related('student__user')

        student_data = []
        submitted_count = 0
        for submission in submissions:
            student_name = submission.student.user.get_full_name() if submission.student and submission.student.user else str(submission.student)
            student_data.append({
                'student': student_name,
                'is_done': submission.is_done,
                'score': submission.score,
                'submitted_at': submission.submitted_at,
            })

            if submission.is_done:
                submitted_count += 1

        total_students = submissions.count()
        completion_rate = (submitted_count / total_students * 100) if total_students > 0 else 0
        avg_score = submissions.aggregate(Avg('score'))['score__avg']

        context = {
            'task': task,
            'submissions': student_data,
            'total_students': total_students,
            'submitted_count': submitted_count,
            'completion_rate': round(completion_rate, 2),
            'avg_score': round(avg_score, 2) if avg_score else None
        }

        if request.accepted_renderer.format == 'html':
            return Response(context, template_name=self.template_name)
        return Response(context)




from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from django.db.models import Avg

class CourseStatsView(APIView):
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = 'teacher/course_stats.html'
    permission_classes = [IsAuthenticated, IsTeacher]

    def get(self, request):
        teacher = request.user.teacher_profile

        # O'qituvchining barcha tasklari
        tasks = Task.objects.filter(teacher=teacher)
        task_list = list(tasks.values('id', 'title'))

        # Barcha talabalar
        students = Student.objects.all()

        result = []
        for student in students:
            task_scores = {}
            for task in tasks:
                submission = TaskSubmission.objects.filter(task=task, student=student).first()
                task_scores[task.title] = submission.score if submission and submission.score is not None else 0

            total_tasks = Task.objects.filter(
                teacher=teacher,
                course__in=student.enrollments.values_list('course', flat=True)
            ).count()

            submitted_tasks = TaskSubmission.objects.filter(
                student=student,
                task__teacher=teacher,
                is_done=True
            ).count()

            completion_rate = round((submitted_tasks / total_tasks) * 100, 2) if total_tasks else 0

            result.append({
                "student": f"{student.name} {student.last_name}",
                "total_tasks": total_tasks,
                "submitted_tasks": submitted_tasks,
                "completion_rate": completion_rate,
                "tasks": task_scores
            })

        context = {
            "tasks": [t['title'] for t in task_list],
            "students": result
        }

        if request.accepted_renderer.format == 'html':
            return Response(context, template_name=self.template_name)
        return Response(context)

class CourseStatsTableView(APIView):
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = 'teacher/course_stats_table.html'
    permission_classes = [IsAuthenticated, IsTeacher]

    def get(self, request, course_id):
        teacher = request.user.teacher_profile
        tasks = Task.objects.filter(teacher=teacher, course_id=course_id).order_by('id')
        task_names = [task.title for task in tasks]

        students = Student.objects.filter(enrollments__course_id=course_id).distinct()
        student_data = []

        for student in students:
            total_tasks = tasks.count()
            submissions = TaskSubmission.objects.filter(student=student, task__in=tasks)

            submitted_tasks = submissions.filter(is_done=True).count()
            completion_rate = round((submitted_tasks / total_tasks) * 100, 2) if total_tasks else 0

            task_scores = {task.title: None for task in tasks}
            for submission in submissions:
                if submission.is_done:
                    task_scores[submission.task.title] = submission.score

            avg_score = (
                submissions.aggregate(avg=Avg('score'))['avg']
                if submitted_tasks > 0 else 0
            )

            student_data.append({
                "student": str(student),
                "total_tasks": total_tasks,
                "submitted_tasks": submitted_tasks,
                "completion_rate": completion_rate,
                "avg_score": round(avg_score or 0, 2),
                "tasks": task_scores
            })

        context = {
            "students": student_data,
            "task_names": task_names
        }

        if request.accepted_renderer.format == 'html':
            return Response(context, template_name=self.template_name)
        return Response(context)

def CourseView(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    tasks = Task.objects.filter(course=course)
    return render(request, 'student_tasks.html', {
        'course': course,
        'tasks': tasks
    })



@require_GET
@ensure_csrf_cookie
def get_csrf_token(request):
    """Get CSRF token for frontend"""
    token = get_token(request)
    return JsonResponse({
        'csrfToken': token,
        'detail': 'CSRF token generated successfully'
    })

# Alternative: Add @ensure_csrf_cookie to your registration views
@ensure_csrf_cookie
def register_student_view(request):
    # Your existing registration logic
    pass