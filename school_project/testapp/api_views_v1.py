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
        test = get_object_or_404(
            Test.objects.prefetch_related("questions__answer_options"),
            id=test_id,
        )

        # Start endpoint should always create a fresh attempt.
        attempt = TestAttempt.objects.create(student=student, test=test)
        questions_payload = []

        for question in test.questions.all():
            answers = list(question.answer_options.all())
            question_payload = {
                "id": question.id,
                "text": question.text,
                "question_type": question.question_type,
                "mark": question.mark,
                "answer_options": [],
            }

            # Choice-like questions: return options without correctness metadata.
            if question.question_type in {"OC", "MC", "ORD", "MAT"}:
                options = []
                for answer in answers:
                    option_payload = {
                        "id": answer.id,
                        "text": answer.text,
                    }
                    if question.question_type == "ORD" and answer.order is not None:
                        option_payload["order"] = answer.order
                    if question.question_type == "MAT" and answer.match_text:
                        option_payload["match_text"] = answer.match_text
                    options.append(option_payload)

                question_payload["answer_options"] = options

            # Written questions: expose only input mode, never expected answer text.
            if question.question_type == "WR":
                input_kind = "text"
                correct_answer = next((a for a in answers if a.is_correct), None)
                if correct_answer:
                    try:
                        Decimal((correct_answer.text or "").strip())
                        input_kind = "numeric"
                    except (InvalidOperation, ValueError):
                        input_kind = "text"
                question_payload["input_kind"] = input_kind

            questions_payload.append(question_payload)

        return Response(
            {
                "attempt_id": attempt.id,
                "test_id": test.id,
                "started_at": attempt.started_at,
                "test": {
                    "id": test.id,
                    "title": test.title,
                    "questions": questions_payload,
                },
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
        teacher = getattr(request.user, "teacher_profile", None)
        if teacher is None:
            return Response(
                {"detail": "Only teachers can access test results."},
                status=status.HTTP_403_FORBIDDEN,
            )

        test = get_object_or_404(
            Test.objects.prefetch_related("questions"),
            id=test_id,
            teacher=teacher,
        )
        attempts = (
            TestAttempt.objects.filter(test=test, completed_at__isnull=False)
            .select_related("student__user")
            .order_by("-completed_at", "-id")
        )
        max_score = sum(
            (Decimal(str(question.mark)) for question in test.questions.all()),
            start=Decimal("0"),
        )

        return Response(
            [
                {
                    "attempt_id": a.id,
                    "student_id": a.student_id,
                    "student_name": str(a.student),
                    "score": a.score,
                    "max_score": float(max_score),
                    "percentage": a.percentage,
                    "completed_at": a.completed_at,
                }
                for a in attempts
            ]
        )


class TeacherAttemptDetailsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, attempt_id: int):
        teacher = getattr(request.user, "teacher_profile", None)
        if teacher is None:
            return Response(
                {"detail": "Only teachers can access attempt details."},
                status=status.HTTP_403_FORBIDDEN,
            )

        attempt = get_object_or_404(
            TestAttempt.objects.select_related("student__user", "test")
            .prefetch_related("test__questions__answer_options"),
            id=attempt_id,
            test__teacher=teacher,
        )

        answers = (
            StudentAnswer.objects.filter(attempt=attempt)
            .select_related("question")
            .prefetch_related("selected_answers")
        )
        answers_by_question_id = {answer.question_id: answer for answer in answers}

        questions = list(attempt.test.questions.all())
        max_score = sum(
            (Decimal(str(question.mark)) for question in questions),
            start=Decimal("0"),
        )

        def map_question_type(question: Question) -> str:
            if question.question_type == "OC":
                return "single"
            if question.question_type == "MC":
                return "multiple"
            if question.question_type == "WR":
                correct_answer = next(
                    (option for option in question.answer_options.all() if option.is_correct),
                    None,
                )
                if correct_answer:
                    try:
                        Decimal((correct_answer.text or "").strip())
                        return "numeric"
                    except (InvalidOperation, ValueError):
                        return "short"
                return "short"
            return "short"

        questions_payload = []
        for question in questions:
            student_answer = answers_by_question_id.get(question.id)
            selected_answers = []
            written_answer = ""
            scored_mark = 0.0

            if student_answer:
                selected_answers = [
                    {"id": selected.id, "text": selected.text}
                    for selected in student_answer.selected_answers.all()
                ]
                written_answer = student_answer.written_answer or ""
                scored_mark = float(student_answer.scored_mark or 0)

            correct_answers = [
                {"id": option.id, "text": option.text}
                for option in question.answer_options.all()
                if option.is_correct
            ]

            questions_payload.append(
                {
                    "question_id": question.id,
                    "prompt": question.text,
                    "question_type": map_question_type(question),
                    "score": scored_mark,
                    "max_score": float(question.mark),
                    "written_answer": written_answer,
                    "selected_answers": selected_answers,
                    "correct_answers": correct_answers,
                }
            )

        return Response(
            {
                "attempt_id": attempt.id,
                "test_id": attempt.test_id,
                "test_title": attempt.test.title,
                "student_id": attempt.student_id,
                "student_name": str(attempt.student),
                "score": attempt.score,
                "max_score": float(max_score),
                "percentage": attempt.percentage,
                "started_at": attempt.started_at,
                "completed_at": attempt.completed_at,
                "questions": questions_payload,
            }
        )
