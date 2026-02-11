from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from schoolapp.models import Enrollment
from .api_serializers import AttemptResultOutputSerializer, AttemptSubmitInputSerializer
from .models import Answer, EnrollmentTest, Question, StudentAnswer, Test, TestAttempt
from .scoring_engine import (
    ChoiceQuestion,
    ComputationalQuestion,
    ShortAnswerQuestion,
    grade_computational,
    grade_multiple_choice_exact,
    grade_short_answer,
    grade_single_choice,
)


class StudentAvailableTestsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        student = request.user.student_profile
        enrollments = Enrollment.objects.filter(student=student)
        tests = Test.objects.filter(
            id__in=EnrollmentTest.objects.filter(
                course__in=enrollments.values_list("course_id", flat=True)
            ).values_list("test_id", flat=True)
        ).distinct()

        payload = [
            {
                "id": t.id,
                "title": t.title,
                "teacher": getattr(t.teacher, "id", None),
                "question_count": t.questions.count(),
                "created_at": t.created_at,
            }
            for t in tests
        ]
        return Response(payload)


class StudentStartAttemptAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, test_id: int):
        student = request.user.student_profile
        test = get_object_or_404(Test, id=test_id)

        attempt, _ = TestAttempt.objects.get_or_create(student=student, test=test)
        return Response(
            {
                "attempt_id": attempt.id,
                "test_id": test.id,
                "started_at": attempt.started_at,
            },
            status=status.HTTP_201_CREATED,
        )


class StudentSubmitAttemptAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, attempt_id: int):
        attempt = get_object_or_404(
            TestAttempt.objects.select_for_update(),
            id=attempt_id,
            student=request.user.student_profile,
        )

        serializer = AttemptSubmitInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        StudentAnswer.objects.filter(attempt=attempt).delete()

        total_score = Decimal("0")
        answers_payload = serializer.validated_data["answers"]

        for item in answers_payload:
            question = get_object_or_404(Question, id=item["question_id"], test=attempt.test)
            selected_ids = item.get("selected_option_ids", [])
            written_answer = item.get("written_answer", "")

            student_answer = StudentAnswer.objects.create(
                attempt=attempt,
                question=question,
                written_answer=written_answer,
                scored_mark=0,
            )

            scoring = self._score_question(question, selected_ids, written_answer)
            student_answer.scored_mark = float(scoring.awarded_points)
            student_answer.save(update_fields=["scored_mark"])

            if selected_ids:
                student_answer.selected_answers.add(*Answer.objects.filter(id__in=selected_ids))

            total_score += scoring.awarded_points

        total_questions = attempt.test.questions.count() or 1
        max_score = sum([Decimal(str(q.mark)) for q in attempt.test.questions.all()], start=Decimal("0"))
        percentage = Decimal("0") if max_score == 0 else (total_score / max_score) * Decimal("100")

        attempt.score = float(total_score)
        attempt.percentage = float(percentage.quantize(Decimal("0.01")))
        attempt.completed_at = timezone.now()
        attempt.save(update_fields=["score", "percentage", "completed_at"])

        response_data = AttemptResultOutputSerializer(
            {
                "attempt_id": attempt.id,
                "score": float(total_score),
                "percentage": float(percentage),
                "total_questions": total_questions,
                "total_answers": len(answers_payload),
            }
        ).data
        return Response(response_data)

    def _score_question(self, question: Question, selected_ids: list[int], written_answer: str):
        points = Decimal(str(question.mark))
        correct_options = set(
            Answer.objects.filter(question=question, is_correct=True).values_list("id", flat=True)
        )

        if question.question_type == "OC":
            return grade_single_choice(
                ChoiceQuestion(points=points, correct_option_ids=correct_options),
                selected_ids,
            )

        if question.question_type == "MC":
            return grade_multiple_choice_exact(
                ChoiceQuestion(points=points, correct_option_ids=correct_options),
                selected_ids,
            )

        # WR fallback for short/computational based on answer metadata
        correct_answer = Answer.objects.filter(question=question, is_correct=True).first()
        if not correct_answer:
            return grade_short_answer(
                ShortAnswerQuestion(points=points, accepted_answers=set(), case_sensitive=False),
                written_answer,
            )

        tolerance = Decimal("0")
        if correct_answer.match_text:
            try:
                tolerance = Decimal(str(correct_answer.match_text))
            except InvalidOperation:
                tolerance = Decimal("0")

        try:
            numeric_value = Decimal((written_answer or "").strip())
            return grade_computational(
                ComputationalQuestion(
                    points=points,
                    expected_answer=Decimal(correct_answer.text.strip()),
                    tolerance=tolerance,
                ),
                numeric_value,
            )
        except (InvalidOperation, ValueError):
            return grade_short_answer(
                ShortAnswerQuestion(
                    points=points,
                    accepted_answers={correct_answer.text},
                    case_sensitive=False,
                ),
                written_answer,
            )


class StudentAttemptResultAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, attempt_id: int):
        attempt = get_object_or_404(TestAttempt, id=attempt_id, student=request.user.student_profile)
        total_answers = StudentAnswer.objects.filter(attempt=attempt).count()
        total_questions = attempt.test.questions.count()
        return Response(
            {
                "attempt_id": attempt.id,
                "test_id": attempt.test_id,
                "score": attempt.score,
                "percentage": attempt.percentage,
                "completed_at": attempt.completed_at,
                "total_questions": total_questions,
                "total_answers": total_answers,
            }
        )


class TeacherTestResultsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, test_id: int):
        test = get_object_or_404(Test, id=test_id, teacher=request.user.teacher_profile)
        attempts = TestAttempt.objects.filter(test=test).select_related("student__user")

        return Response(
            [
                {
                    "attempt_id": a.id,
                    "student_id": a.student_id,
                    "student_name": str(a.student),
                    "score": a.score,
                    "percentage": a.percentage,
                    "completed_at": a.completed_at,
                }
                for a in attempts
            ]
        )
