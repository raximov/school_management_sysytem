from django.urls import path, include
from django.views.generic import TemplateView
from rest_framework.routers import DefaultRouter

from .api_views_v1 import (
    StudentAvailableTestsAPIView,
    StudentStartAttemptAPIView,
    StudentSubmitAttemptAPIView,
    StudentAttemptResultAPIView,
    TeacherTestResultsAPIView as TeacherTestResultsAPIV1,
)
from .views import (
    StudentAssignedTestsView, SubmitAnswersView, StudentTestResultView,\
    TeacherTestResultsView,  submit_test_view, \
    TeacherTestHTMLView, TestViewSet, student_test_attempts_view, QuestionViewSet,\
     student_tests_view, EnrollmentTestViewSet, AnswerViewSet, TeacherTestHTMLView,\
    teacher_tests, teacher_questions, teacher_answers, TeacherTestResultsView,\
    teacher_panel, student_test_detail_view, submit_test_view, test_results_view, attempt_detail_view,\

)
app_name = 'testapp'  # app namespace

router = DefaultRouter()
router.register(r'teacher/tests', TestViewSet, basename='teacher-tests')
router.register(r'teacher/answers', AnswerViewSet, basename='teacher-answers')
router.register(r'teacher/questions', QuestionViewSet, basename='teacher-questions')
router.register(r'teacher/enrollment', EnrollmentTestViewSet, basename='teacher-enrollment-tests')
router.register(r'enrollment-tests', EnrollmentTestViewSet, basename='enrollment-test')

urlpatterns = [
    path('api/v1/student/tests/', StudentAvailableTestsAPIView.as_view(), name='api_v1_student_tests'),
    path('api/v1/student/tests/<int:test_id>/start/', StudentStartAttemptAPIView.as_view(), name='api_v1_student_start_attempt'),
    path('api/v1/student/attempts/<int:attempt_id>/submit/', StudentSubmitAttemptAPIView.as_view(), name='api_v1_student_submit_attempt'),
    path('api/v1/student/attempts/<int:attempt_id>/result/', StudentAttemptResultAPIView.as_view(), name='api_v1_student_attempt_result'),
    path('api/v1/teacher/tests/<int:test_id>/results/', TeacherTestResultsAPIV1.as_view(), name='api_v1_teacher_test_results'),
    path('teacher/enrollment/', TemplateView.as_view(template_name="teacher/enrollment_test_crud.html"), name='enrollment_test_crud'),

    path('teacher-panel/', teacher_panel, name='teacher-panel'),



    path('teacher/', include(router.urls)),  # Use the router for teacher tests
    path('teacher/test/<int:test_id>/result/', test_results_view, name='test_results'),

    path('teacher/attempt/<int:attempt_id>/details/', attempt_detail_view, name='attempt_detail'),


    # path('teacher/tests/', teacher_tests, name='teacher_tests'),
    # path('teacher/tests/<int:test_id>/questions/', teacher_questions, name='teacher_questions'),
    # path('teacher/questions/<int:question_id>/answers/', teacher_answers, name='teacher_answers'),


    path('teacher/test/<int:test_id>/results/', TeacherTestResultsView.as_view(), name='teacher_test_results'),
    path('teacher/tests/html/', TeacherTestHTMLView.as_view(), name='teacher_test_list_html'),
    # path('teacher/enrollments/', EnrollmentTestViewSet.as_view({'get': 'list'}), name='teacher_enrollments'),

    path('student/tests/', student_tests_view, name='student_tests'),
    path('student/tests/<int:test_id>/', student_test_detail_view, name='student_test_detail'),
    path('student/tests/<int:test_id>/submit/', submit_test_view, name='submit_test'),



    path('student/test/', StudentAssignedTestsView.as_view(), name='student-tests'),
    path('student/tests/<int:attempt_id>/submit/', SubmitAnswersView.as_view(), name='submit-answers'),
    path('student/test/<int:test_id>/result/', StudentTestResultView.as_view(), name='student_test_result'),
    
    path('student/submit-test/', submit_test_view, name='submit_student_test'),
    path('student/attempts/', student_test_attempts_view, name='student_test_attempts'),
  
]

urlpatterns += router.urls