from django.urls import path
from django.contrib.auth.views import LogoutView
from .views import (
    register_student, register_teacher, student_dashboard, teacher_dashboard,
    CustomLoginView, post_login_redirect, dashboard_redirect,
    MyProtectedView, MyPublicView, StudentTasksListView, StudentTasksView, SubmitTaskView,TeacherTaskViewSet,TeacherSubmitView, TeacherSubmitRetrieveUpdateDestroyView, TeacherSubmitListCreateView, CourseStatsView, CourseView, course_stats_table, TaskStatsTableView
)

urlpatterns = [
    path('register/student/', register_student, name='register_student'),
    path('register/teacher/', register_teacher, name='register_teacher'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='/login/'), name='logout'),
    path('dashboard/', dashboard_redirect, name='dashboard'),
    path('student/', student_dashboard, name='student_dashboard'),
    path('teacher/', teacher_dashboard, name='teacher_dashboard'),
    path('redirect/', post_login_redirect, name='post_login_redirect'),
    path('api/protected/', MyProtectedView.as_view(), name='api_protected'),
    path('api/public/', MyPublicView.as_view(), name='api_public'),
    path('student/tasks/', StudentTasksListView.as_view(), name='student_tasks'),
    path('student/tasks/<int:pk>/', StudentTasksView.as_view(), name='submit_task'),
    path('student/submit/', SubmitTaskView.as_view(), name='submit'),
    path('student/submit/<int:pk>/', SubmitTaskView.as_view(), name='submit_task'),
    path('teacher/tasks/', TeacherTaskViewSet.as_view({'get': 'list','post': 'create'}), name='teacher_tasks'),
    path('teacher/tasks/<int:pk>/', TeacherTaskViewSet.as_view({'get': 'list', 'post': 'create'}), name='teacher_submit_task'),
    path('teacher/submit/', TeacherSubmitListCreateView.as_view(), name='teacher_submit_task_list'),
    path('teacher/submit/<int:pk>/', TeacherSubmitRetrieveUpdateDestroyView.as_view(), name='teacher_submit_task_retrieve'),
    # path('teacher/task-stats/', TaskStatsView.as_view(), name='teacher-task-stats'),
    path('course/', CourseView.as_view({'get':'list','post':'create','put':'update'}), name='course_view'),
    path('teacher/course-stats/', CourseStatsView.as_view()),
    path('teacher/course-stats/<int:course_id>/', course_stats_table, name='course_stats_table'),
    path('teacher/task-stats/<int:pk>/', TaskStatsTableView.as_view(), name='task_stats_detail'),

]