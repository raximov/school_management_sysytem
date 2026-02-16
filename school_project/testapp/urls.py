from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .api_views_v1 import (
    StudentAttemptResultAPIView,
    StudentAvailableTestsAPIView,
    StudentStartAttemptAPIView,
    StudentSubmitAttemptAPIView,
    TeacherAttemptDetailsAPIView as TeacherAttemptDetailsAPIV1,
    TeacherTestResultsAPIView as TeacherTestResultsAPIV1,
)
from .views import (
    AnswerViewSet,
    EnrollmentTestViewSet,
    QuestionViewSet,
    StudentAssignedTestsView,
    StudentTestResultView,
    SubmitAnswersView,
    TeacherTestResultsView,
    TestViewSet,
)

app_name = "testapp"

router = DefaultRouter()
router.register(r"teacher/tests", TestViewSet, basename="teacher-tests")
router.register(r"teacher/answers", AnswerViewSet, basename="teacher-answers")
router.register(r"teacher/questions", QuestionViewSet, basename="teacher-questions")
router.register(r"teacher/enrollment", EnrollmentTestViewSet, basename="teacher-enrollment-tests")
router.register(r"enrollment-tests", EnrollmentTestViewSet, basename="enrollment-test")

urlpatterns = [
    # v1 JSON API
    path("api/v1/student/tests/", StudentAvailableTestsAPIView.as_view(), name="api_v1_student_tests"),
    path("api/v1/student/tests/<int:test_id>/start/", StudentStartAttemptAPIView.as_view(), name="api_v1_student_start_attempt"),
    path("api/v1/student/attempts/<int:attempt_id>/submit/", StudentSubmitAttemptAPIView.as_view(), name="api_v1_student_submit_attempt"),
    path("api/v1/student/attempts/<int:attempt_id>/result/", StudentAttemptResultAPIView.as_view(), name="api_v1_student_attempt_result"),
    path("api/v1/teacher/tests/<int:test_id>/results/", TeacherTestResultsAPIV1.as_view(), name="api_v1_teacher_test_results"),
    path(
        "api/v1/teacher/attempts/<int:attempt_id>/details/",
        TeacherAttemptDetailsAPIV1.as_view(),
        name="api_v1_teacher_attempt_details",
    ),
    # Legacy JSON API that frontend already uses
    path("teacher/test/<int:test_id>/results/", TeacherTestResultsView.as_view(), name="teacher_test_results"),
    path("student/test/", StudentAssignedTestsView.as_view(), name="student-tests"),
    path("student/tests/<int:attempt_id>/submit/", SubmitAnswersView.as_view(), name="submit-answers"),
    path("student/test/<int:test_id>/result/", StudentTestResultView.as_view(), name="student_test_result"),
    # Explicit aliases for assignment API to avoid HTML route clashes
    path(
        "teacher/enrollment-tests/",
        EnrollmentTestViewSet.as_view({"get": "list", "post": "create"}),
        name="teacher_enrollment_tests",
    ),
    path(
        "teacher/enrollment-tests/<int:pk>/",
        EnrollmentTestViewSet.as_view(
            {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
        ),
        name="teacher_enrollment_test_detail",
    ),
    # Router endpoints
    path("", include(router.urls)),
]
