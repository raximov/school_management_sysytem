from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    StudentAssignedTestsView, SubmitAnswersView, StudentTestResultView, TeacherTestResultsView, student_random_test_view, submit_test_view,  TeacherTestHTMLView, TestViewSet, student_test_attempts_view
)

router = DefaultRouter()
router.register(r'teacher/tests', TestViewSet, basename='teacher-tests')

urlpatterns = [
    path('student/tests/', StudentAssignedTestsView.as_view(), name='student-tests'),
    path('student/tests/<int:attempt_id>/submit/', SubmitAnswersView.as_view(), name='submit-answers'),
    path('student/test/<int:test_id>/result/', StudentTestResultView.as_view(), name='student_test_result'),
    path('teacher/test/<int:test_id>/results/', TeacherTestResultsView.as_view(), name='teacher_test_results'),
    path('student/random-tests/', student_random_test_view, name='student_random_tests'),
    path('student/submit-test/', submit_test_view, name='submit_student_test'),
    path('teacher/tests/html/', TeacherTestHTMLView.as_view(), name='teacher_test_list_html'),
    path('test/student/attempts/', student_test_attempts_view, name='student_test_attempts'),

  
]
urlpatterns += router.urls