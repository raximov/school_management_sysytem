from rest_framework import viewsets
from rest_framework.generics import RetrieveUpdateDestroyAPIView, ListCreateAPIView
from django.db.models import Count, Q, F, FloatField, ExpressionWrapper,Avg
from collections import defaultdict
from django.db.models import OuterRef, Subquery
from django.db.models.functions import Coalesce
from django.urls import reverse_lazy
from urllib.parse import parse_qsl
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET
from datetime import timedelta
import json
import hashlib
import hmac
import time
import os
from django.shortcuts import get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect
from django.contrib.auth.models import User

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.conf import settings
from django.db import DatabaseError
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login
from django.utils import timezone

from django.utils.decorators import method_decorator

from .forms import StudentRegisterForm  # Make sure this exists
from .permissions import IsStudent, IsTeacher, IsAuthenticated
from .models import Department, Classroom, Teacher, Student, Course, Enrollment, Task, TaskSubmission
from .serializers import (
    DepartmentSerializer, ClassroomSerializer,
    TeacherSerializer, StudentSerializer,
    CourseSerializer, EnrollmentSerializer, TaskSerializer, StudentSubmissionSerializer, TeacherSubmissionSerializer, StudentTaskStatsSerializer, 
)


def _database_error_response(exc):
    detail = "Database is not ready. Check DB env variables and run migrations."
    if settings.DEBUG:
        detail = f"Database error: {exc}"
    return Response({"detail": detail}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SafeObtainAuthToken(ObtainAuthToken):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        try:
            return super().post(request, *args, **kwargs)
        except DatabaseError as exc:
            return _database_error_response(exc)
        except Exception as exc:  # noqa: BLE001
            detail = "Auth endpoint failed before token creation."
            if settings.DEBUG:
                detail = f"Auth endpoint error: {exc}"
            return Response({"detail": detail}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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


class RegisterStudentView(APIView):
    permission_classes = [AllowAny]
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = 'accounts/register_student.html'

    def get(self, request):
        form = StudentRegisterForm()
        return Response({'form': form}, template_name=self.template_name)

    def post(self, request):
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
                return redirect('student_profile')
        return Response({'form': form}, template_name=self.template_name)

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
                return redirect('student_profile')
    else:
        form = StudentRegisterForm()
    return render(request, 'accounts/register_student.html', {'form': form})

class RegisterTeacherView(APIView):
    permission_classes = [AllowAny]
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = 'accounts/register_teacher.html'

    def get(self, request):
        form = UserCreationForm()
        return Response({'form': form}, template_name=self.template_name)

    def post(self, request):
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
            return redirect('teacher_profile')
        return Response({'form': form}, template_name=self.template_name)
    
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
            return redirect('teacher_profile')
    else:
        form = UserCreationForm()
    return render(request, 'accounts/register_teacher.html', {'form': form})


class CustomLoginAPIView(APIView):
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = 'accounts/login.html'

    def get(self, request):
        # HTML sahifa render
        if request.user.is_authenticated:
            if hasattr(request.user, 'student_profile'):
                redirect_url = reverse_lazy('student_profile')
            elif hasattr(request.user, 'teacher_profile'):
                redirect_url = reverse_lazy('teacher_profile')
            else:
                redirect_url = reverse_lazy('home')
            return Response({"authenticated": True, "redirect_url": str(redirect_url)})

        # Sahifani HTML bilan render qilish
        return Response({}, template_name=self.template_name)

    def post(self, request):
        # HTML form POST bo‘lsa request.data o‘rniga request.POST ishlatish xavfsiz
        username = request.POST.get("username") or request.data.get("username")
        password = request.POST.get("password") or request.data.get("password")

        if not username or not password:
            return Response(
                {"error": "Username and password are required."},
                status=status.HTTP_400_BAD_REQUEST,
                template_name=self.template_name
            )

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if hasattr(user, 'student_profile'):
                redirect_url = reverse_lazy('student_profile')
            elif hasattr(user, 'teacher_profile'):
                redirect_url = reverse_lazy('teacher_profile')
            else:
                redirect_url = reverse_lazy('home')

            # Agar HTML form POST bo‘lsa, redirect qilish
            if request.accepted_renderer.format == 'html':
                return redirect(redirect_url)

            # Agar API POST bo‘lsa, JSON qaytarish
            return Response({
                "detail": "Login successful",
                "redirect_url": str(redirect_url)
            }, status=status.HTTP_200_OK)

        return Response(
            {"error": "Invalid username or password."},
            status=status.HTTP_401_UNAUTHORIZED,
            template_name=self.template_name
        )


class TelegramWebAppLoginAPIView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        init_data = (request.data.get("initData") or "").strip()
        role_hint = (request.data.get("roleHint") or "student").strip().lower()
        bot_token = (os.getenv("TELEGRAM_BOT_TOKEN") or "").strip()
        max_age = self._parse_max_age(os.getenv("TELEGRAM_AUTH_MAX_AGE_SEC", "86400"))

        if not init_data:
            return Response({"detail": "initData is required."}, status=status.HTTP_400_BAD_REQUEST)

        if not bot_token:
            return Response({"detail": "TELEGRAM_BOT_TOKEN is not configured."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            telegram_user = self._validate_init_data(init_data, bot_token, max_age)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_401_UNAUTHORIZED)

        telegram_id = telegram_user["id"]
        username = f"tg_{telegram_id}"
        first_name = (telegram_user.get("first_name") or "").strip()
        last_name = (telegram_user.get("last_name") or "").strip()

        try:
            user, created = User.objects.get_or_create(username=username)
            if created:
                user.first_name = first_name
                user.last_name = last_name
                user.email = f"{username}@telegram.local"
                user.set_unusable_password()
                user.save(update_fields=["first_name", "last_name", "email", "password"])
            else:
                changed_fields = []
                if first_name and user.first_name != first_name:
                    user.first_name = first_name
                    changed_fields.append("first_name")
                if last_name and user.last_name != last_name:
                    user.last_name = last_name
                    changed_fields.append("last_name")
                if changed_fields:
                    user.save(update_fields=changed_fields)

            role = self._ensure_role_profile(user, role_hint, first_name, last_name, telegram_id)
            token, _ = Token.objects.get_or_create(user=user)
        except DatabaseError as exc:
            return _database_error_response(exc)

        return Response(
            {
                "token": token.key,
                "role": role,
                "expiresAt": (timezone.now() + timedelta(hours=8)).isoformat(),
            },
            status=status.HTTP_200_OK,
        )

    def _ensure_role_profile(self, user, role_hint, first_name, last_name, telegram_id):
        if hasattr(user, "teacher_profile"):
            return "teacher"
        if hasattr(user, "student_profile"):
            return "student"

        teacher_ids = self._parse_teacher_ids(os.getenv("TELEGRAM_TEACHER_IDS", ""))
        if role_hint == "teacher" and str(telegram_id) in teacher_ids:
            Teacher.objects.create(
                user=user,
                name=first_name or "Teacher",
                last_name=last_name or "User",
                email=user.email or f"{user.username}@telegram.local",
            )
            return "teacher"

        Student.objects.create(
            user=user,
            name=first_name or "Student",
            last_name=last_name or "User",
        )
        return "student"

    def _parse_teacher_ids(self, raw_value):
        return {item.strip() for item in raw_value.split(",") if item.strip()}

    def _parse_max_age(self, value):
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return 86400
        return max(60, parsed)

    def _validate_init_data(self, init_data, bot_token, max_age):
        parts = dict(parse_qsl(init_data, keep_blank_values=True))
        provided_hash = parts.pop("hash", "")
        if not provided_hash:
            raise ValueError("hash is missing in initData.")

        auth_date_raw = parts.get("auth_date")
        if not auth_date_raw:
            raise ValueError("auth_date is missing in initData.")

        try:
            auth_date = int(auth_date_raw)
        except (TypeError, ValueError):
            raise ValueError("auth_date is invalid.") from None

        now_ts = int(time.time())
        if now_ts - auth_date > max_age:
            raise ValueError("initData expired.")

        data_check_string = "\n".join(f"{key}={value}" for key, value in sorted(parts.items()))
        secret_key = hmac.new(b"WebAppData", bot_token.encode("utf-8"), hashlib.sha256).digest()
        calculated_hash = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()

        if not hmac.compare_digest(calculated_hash, provided_hash):
            raise ValueError("Invalid Telegram signature.")

        user_raw = parts.get("user")
        if not user_raw:
            raise ValueError("user payload is missing in initData.")

        try:
            user_data = json.loads(user_raw)
        except json.JSONDecodeError:
            raise ValueError("user payload is invalid JSON.") from None

        if not isinstance(user_data, dict) or "id" not in user_data:
            raise ValueError("user payload is invalid.")

        return user_data



class CustomLogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]
    next_page = None  # default value

    def post(self, request):
        from django.contrib.auth import logout
        from django.urls import reverse_lazy

        logout(request)
        redirect_url = reverse_lazy(self.next_page or 'login')
        return Response({"detail": "Logged out successfully", "redirect_url": str(redirect_url)})



class PostLoginRedirectAPIView(APIView):
    permission_classes = [IsAuthenticated]
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = 'accounts/login.html'

    def get(self, request):
        if hasattr(request.user, 'student_profile'):
            return Response({"redirect_url": reverse_lazy('student_profile')})
        elif hasattr(request.user, 'teacher_profile'):
            return Response({"redirect_url": reverse_lazy('teacher_profile')})
        return Response({"redirect_url": reverse_lazy('home')})


class StudentProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = 'student_profile.html'

    def get(self, request):
        if not hasattr(request.user, 'student_profile'):
            return Response({"error": "You are not authorized to view this page."}, status=status.HTTP_403_FORBIDDEN)

        student = Student.objects.filter(user=request.user).first()
        if not student:
            return Response({"error": "Student profile not found."}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            "id": student.id,
            "name": student.user.get_full_name(),
            "email": student.user.email,
            # Add other student fields here
        })


class TeacherProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = 'accounts/teacher_profile.html'

    def get(self, request):
        if not hasattr(request.user, 'teacher_profile'):
            return Response({"error": "You are not authorized to view this page."}, status=status.HTTP_403_FORBIDDEN)

        teacher = Teacher.objects.filter(user=request.user).first()
        if not teacher:
            return Response({"error": "Teacher profile not found."}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            "id": teacher.id,
            "name": teacher.user.get_full_name(),
            "email": teacher.user.email,
            # Add other teacher fields here
        })


class ProfileRedirectAPIView(APIView):
    permission_classes = [IsAuthenticated]
    renderer_classes = [TemplateHTMLRenderer]

    def get(self, request):
        if hasattr(request.user, 'student_profile'):
            return Response({}, template_name='accounts/student_profile.html')
        elif hasattr(request.user, 'teacher_profile'):
            return Response({}, template_name='accounts/teacher_profile.html')
        return Response({}, template_name='home.html')


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


class FrontendMockDataAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        from testapp.models import Test

        limit = self._parse_limit(request.query_params.get("limit"))
        students = Student.objects.select_related("user").order_by("id")[:limit]
        courses = Course.objects.select_related("teacher__user").order_by("id")[:limit]
        enrollments = Enrollment.objects.select_related("student", "course").order_by("id")[:limit]
        tasks = Task.objects.select_related("course", "teacher").order_by("id")[:limit]
        tests = (
            Test.objects.select_related("teacher__user")
            .annotate(question_count=Count("questions"))
            .order_by("id")[:limit]
        )

        def student_name(student):
            if student.user:
                full_name = student.user.get_full_name().strip()
                if full_name:
                    return full_name
            fallback = " ".join(part for part in [student.name, student.last_name] if part).strip()
            return fallback or f"Student {student.id}"

        def teacher_name(teacher):
            if teacher and teacher.user:
                full_name = teacher.user.get_full_name().strip()
                if full_name:
                    return full_name
            if not teacher:
                return ""
            fallback = " ".join(part for part in [teacher.name, teacher.last_name] if part).strip()
            return fallback or f"Teacher {teacher.id}"

        payload = {
            "source": "database",
            "summary": {
                "students": Student.objects.count(),
                "courses": Course.objects.count(),
                "enrollments": Enrollment.objects.count(),
                "tasks": Task.objects.count(),
                "tests": Test.objects.count(),
            },
            "students": [
                {
                    "id": student.id,
                    "name": student_name(student),
                    "email": student.email or (student.user.email if student.user else ""),
                }
                for student in students
            ],
            "courses": [
                {
                    "id": course.id,
                    "title": course.title,
                    "teacher_id": course.teacher_id,
                    "teacher_name": teacher_name(course.teacher),
                    "schedule": course.schedule,
                }
                for course in courses
            ],
            "enrollments": [
                {
                    "id": enrollment.id,
                    "student_id": enrollment.student_id,
                    "course_id": enrollment.course_id,
                }
                for enrollment in enrollments
            ],
            "tasks": [
                {
                    "id": task.id,
                    "title": task.title,
                    "course_id": task.course_id,
                    "teacher_id": task.teacher_id,
                    "max_score": task.max_score,
                    "due_date": task.due_date.isoformat() if task.due_date else None,
                }
                for task in tasks
            ],
            "tests": [
                {
                    "id": test.id,
                    "title": test.title,
                    "teacher_id": test.teacher_id,
                    "teacher_name": teacher_name(test.teacher),
                    "question_count": test.question_count,
                    "created_at": test.created_at.isoformat() if test.created_at else None,
                }
                for test in tests
            ],
        }

        if all(
            not payload[key]
            for key in ["students", "courses", "enrollments", "tasks", "tests"]
        ):
            payload.update(self._fallback_payload())
            payload["source"] = "fallback"
            payload["summary"] = {
                "students": len(payload["students"]),
                "courses": len(payload["courses"]),
                "enrollments": len(payload["enrollments"]),
                "tasks": len(payload["tasks"]),
                "tests": len(payload["tests"]),
            }

        return Response(payload, status=status.HTTP_200_OK)

    def _parse_limit(self, raw_limit):
        try:
            limit = int(raw_limit) if raw_limit is not None else 20
        except (TypeError, ValueError):
            limit = 20
        return max(1, min(limit, 100))

    def _fallback_payload(self):
        return {
            "students": [
                {"id": 1, "name": "Ali Valiyev", "email": "ali@student.local"},
                {"id": 2, "name": "Laylo Karimova", "email": "laylo@student.local"},
            ],
            "courses": [
                {
                    "id": 1,
                    "title": "Mathematics",
                    "teacher_id": 1,
                    "teacher_name": "John Doe",
                    "schedule": {"days": [1, 3, 5], "time": "09:00 - 10:30"},
                },
                {
                    "id": 2,
                    "title": "Physics",
                    "teacher_id": 2,
                    "teacher_name": "Jane Smith",
                    "schedule": {"days": [2, 4], "time": "11:00 - 12:30"},
                },
            ],
            "enrollments": [
                {"id": 1, "student_id": 1, "course_id": 1},
                {"id": 2, "student_id": 1, "course_id": 2},
                {"id": 3, "student_id": 2, "course_id": 1},
            ],
            "tasks": [
                {
                    "id": 1,
                    "title": "Algebra Worksheet",
                    "course_id": 1,
                    "teacher_id": 1,
                    "max_score": 100,
                    "due_date": "2026-03-01",
                },
                {
                    "id": 2,
                    "title": "Newton Laws Lab",
                    "course_id": 2,
                    "teacher_id": 2,
                    "max_score": 100,
                    "due_date": "2026-03-05",
                },
            ],
            "tests": [
                {
                    "id": 1,
                    "title": "Math Quiz 1",
                    "teacher_id": 1,
                    "teacher_name": "John Doe",
                    "question_count": 10,
                    "created_at": "2026-02-10T09:00:00Z",
                },
                {
                    "id": 2,
                    "title": "Physics Quiz 1",
                    "teacher_id": 2,
                    "teacher_name": "Jane Smith",
                    "question_count": 8,
                    "created_at": "2026-02-11T10:30:00Z",
                },
            ],
        }

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
