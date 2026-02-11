# Telegram Mini App Educational Testing Platform (Production Architecture)

## 1. System Architecture Overview

### Can we use PostgreSQL instead of SQLite?
Yes — and for production you **should**. PostgreSQL is strongly recommended for:
- concurrent writes (attempt submissions, analytics)
- row-level locking and transactional safety
- indexing/partitioning options for large attempts tables
- robust backups and replication

### High-level architecture

```text
[Telegram Client]
    -> [Mini App (React + Telegram WebApp SDK)]
    -> [API Gateway / Nginx]
    -> [Django + DRF API]
        -> Auth Module (Telegram initData + JWT)
        -> Test Management Module
        -> Attempt & Scoring Module
        -> Analytics Module
        -> Notifications / Events (optional queue)
    -> [PostgreSQL]
    -> [Redis] (cache, rate-limit, async queue backend)
```

### Recommended backend module boundaries (clean architecture)
- `accounts`: Telegram identity, role assignment, JWT login, profile
- `assessments`: tests, questions, options, publishing
- `attempts`: attempt lifecycle, answer submission, finalization
- `scoring`: deterministic grading engine, explainable score breakdown
- `analytics`: aggregates for teacher dashboards

### Telegram login flow
1. Mini App opens in Telegram and obtains `Telegram.WebApp.initData`.
2. Frontend sends `initData` to backend `POST /api/v1/auth/telegram/login`.
3. Backend verifies HMAC signature using bot token.
4. Backend upserts user and profile (`Teacher` or `Student`).
5. Backend returns JWT access/refresh + role + profile metadata.

---

## 2. Database Schema Design (ERD-level)

### Core entities
- **User** (`auth_user` + `Profile` extension)
- **Role** (`teacher`, `student`)
- **Course** (optional for grouping tests)
- **Test**
- **Question**
- **QuestionOption** (for choice questions)
- **TestAssignment** (test availability for student/cohort)
- **Attempt**
- **AttemptAnswer**
- **AttemptScoreDetail** (audit trail per question)

### Relationship summary
- Teacher 1..N Test
- Test 1..N Question
- Question 1..N QuestionOption (for single/multiple)
- Student 1..N Attempt
- Attempt 1..N AttemptAnswer
- Attempt N..1 Test
- AttemptScoreDetail 1..1 per `Attempt x Question`

### Suggested PostgreSQL indexing
- `attempt(student_id, status, started_at desc)`
- `attempt(test_id, submitted_at desc)`
- `attempt_answer(attempt_id, question_id)` unique
- `question(test_id, order_no)`
- partial index for published tests: `test(is_published) where is_published=true`

---

## 3. Django Models

Use/align with these production models (you can keep existing app names but this is the target shape):

```python
# assessments/models.py
from decimal import Decimal
from django.conf import settings
from django.db import models
from django.utils import timezone


class UserRole(models.TextChoices):
    TEACHER = "teacher", "Teacher"
    STUDENT = "student", "Student"


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    telegram_id = models.BigIntegerField(unique=True, db_index=True)
    username = models.CharField(max_length=128, blank=True)
    role = models.CharField(max_length=16, choices=UserRole.choices)
    photo_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Test(models.Model):
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_tests")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    time_limit_seconds = models.PositiveIntegerField(default=900)
    passing_score = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("60.00"))
    randomize_questions = models.BooleanField(default=False)
    randomize_options = models.BooleanField(default=False)
    is_published = models.BooleanField(default=False, db_index=True)
    allow_partial_scoring = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class QuestionType(models.TextChoices):
    SINGLE = "single", "Single Choice"
    MULTIPLE = "multiple", "Multiple Choice"
    SHORT = "short", "Short Answer"
    COMPUTATIONAL = "computational", "Computational"


class Question(models.Model):
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name="questions")
    qtype = models.CharField(max_length=20, choices=QuestionType.choices)
    prompt = models.TextField()
    points = models.DecimalField(max_digits=6, decimal_places=2)
    explanation = models.TextField(blank=True)
    order_no = models.PositiveIntegerField(default=1)

    # short-answer config
    accepted_text_answers = models.JSONField(default=list, blank=True)
    case_sensitive = models.BooleanField(default=False)

    # computational config
    expected_numeric_answer = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    numeric_tolerance = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)


class QuestionOption(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="options")
    text = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)
    order_no = models.PositiveIntegerField(default=1)


class AttemptStatus(models.TextChoices):
    IN_PROGRESS = "in_progress", "In Progress"
    SUBMITTED = "submitted", "Submitted"
    GRADED = "graded", "Graded"
    EXPIRED = "expired", "Expired"


class Attempt(models.Model):
    test = models.ForeignKey(Test, on_delete=models.PROTECT, related_name="attempts")
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="attempts")
    status = models.CharField(max_length=16, choices=AttemptStatus.choices, default=AttemptStatus.IN_PROGRESS, db_index=True)
    started_at = models.DateTimeField(default=timezone.now)
    submitted_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField()
    score = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("0.00"))
    max_score = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("0.00"))
    percentage = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal("0.00"))
    passed = models.BooleanField(default=False)

    class Meta:
        indexes = [models.Index(fields=["student", "status", "started_at"])]


class AttemptAnswer(models.Model):
    attempt = models.ForeignKey(Attempt, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(Question, on_delete=models.PROTECT)
    selected_option_ids = models.JSONField(default=list, blank=True)  # for single/multiple
    text_answer = models.TextField(blank=True)
    numeric_answer = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    is_correct = models.BooleanField(default=False)
    awarded_points = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("0.00"))
    feedback = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["attempt", "question"], name="uq_attempt_question")
        ]
```

---

## 4. Serializers

```python
# assessments/serializers.py
from rest_framework import serializers
from .models import Test, Question, QuestionOption, Attempt, AttemptAnswer


class QuestionOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionOption
        fields = ["id", "text", "order_no"]


class QuestionSerializer(serializers.ModelSerializer):
    options = QuestionOptionSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = [
            "id", "qtype", "prompt", "points", "explanation", "order_no",
            "accepted_text_answers", "case_sensitive", "numeric_tolerance", "options"
        ]


class TestSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Test
        fields = [
            "id", "title", "description", "time_limit_seconds", "passing_score",
            "randomize_questions", "randomize_options", "is_published", "allow_partial_scoring", "questions"
        ]


class AttemptAnswerUpsertSerializer(serializers.Serializer):
    question_id = serializers.IntegerField()
    selected_option_ids = serializers.ListField(child=serializers.IntegerField(), required=False)
    text_answer = serializers.CharField(required=False, allow_blank=True)
    numeric_answer = serializers.DecimalField(required=False, max_digits=18, decimal_places=6)


class AttemptSubmitSerializer(serializers.Serializer):
    answers = AttemptAnswerUpsertSerializer(many=True)


class AttemptResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attempt
        fields = ["id", "status", "score", "max_score", "percentage", "passed", "submitted_at"]
```

---

## 5. API Views

Recommended endpoints (`/api/v1/...`):

### Auth
- `POST /auth/telegram/login` → verify `initData`, issue JWT
- `POST /auth/refresh` → refresh token

### Teacher
- `GET/POST /teacher/tests`
- `GET/PATCH/DELETE /teacher/tests/{id}`
- `POST /teacher/tests/{id}/publish`
- `POST /teacher/tests/{id}/questions`
- `GET /teacher/tests/{id}/results`
- `GET /teacher/tests/{id}/analytics`

### Student
- `GET /student/tests` (available + published)
- `POST /student/tests/{id}/attempts/start`
- `PATCH /student/attempts/{attempt_id}/answers` (autosave)
- `POST /student/attempts/{attempt_id}/submit`
- `GET /student/attempts/{attempt_id}/result`

### Role permissions
- `IsAuthenticated`
- `IsTeacher` for test management and analytics
- `IsStudent` for attempt lifecycle
- object-level validation ensures teacher can mutate only own tests

Pseudo-view for submit endpoint:

```python
class StudentAttemptSubmitAPIView(APIView):
    permission_classes = [IsAuthenticated, IsStudent]

    @transaction.atomic
    def post(self, request, attempt_id):
        attempt = get_object_or_404(Attempt.objects.select_for_update(), id=attempt_id, student=request.user)
        if attempt.status != AttemptStatus.IN_PROGRESS:
            return Response({"detail": "Attempt already finalized"}, status=400)

        serializer = AttemptSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        upsert_answers(attempt, serializer.validated_data["answers"])
        score_attempt(attempt)
        attempt.status = AttemptStatus.SUBMITTED
        attempt.submitted_at = timezone.now()
        attempt.save(update_fields=["status", "submitted_at", "score", "max_score", "percentage", "passed"])

        return Response(AttemptResultSerializer(attempt).data)
```

---

## 6. Scoring Engine Implementation

A concrete reusable engine is implemented in `school_project/testapp/scoring_engine.py` with:
- single-choice exact validation
- multiple-choice exact or partial scoring
- short-answer case-sensitive/insensitive match
- computational tolerance-based numeric matching

Use this service in submit/finalize flow and persist per-question `awarded_points` for explainability.

---

## 7. Example Test Cases

1. **Single-choice**
   - Correct option chosen → full points
   - Wrong or multiple options selected → zero

2. **Multiple-choice exact**
   - All correct and no extra selected → full points
   - Any mismatch → zero

3. **Multiple-choice partial**
   - +fraction for each correct selected
   - −fraction for each incorrect selected (clamped at 0)

4. **Short-answer**
   - "Photosynthesis" vs input "photosynthesis" with `case_sensitive=False` → correct

5. **Computational**
   - expected 3.14159, tolerance 0.01
   - student 3.14 → correct

---

## 8. Unit Testing Code

Scoring unit tests are added in `school_project/testapp/tests_scoring_engine.py` and cover:
- all 4 question types
- partial scoring behavior
- tolerance matching
- validation errors / edge behavior

For integration tests (recommended):
- JWT auth with Telegram login mock
- teacher CRUD over tests/questions
- student start→autosave→submit lifecycle
- object permission failures (student editing teacher resources)

---

## 9. Deployment Considerations

### PostgreSQL migration plan
1. Add env-driven DB config in Django settings.
2. Provision PostgreSQL with separate db/user.
3. Run migrations + data migration from SQLite if needed.
4. Add pgBouncer for connection pooling.

### Infra
- Gunicorn + Nginx
- Redis (cache + Celery)
- Celery worker for analytics aggregation and asynchronous notifications
- Sentry for error monitoring
- Prometheus/Grafana metrics

### Security checklist
- Verify Telegram initData HMAC on every login
- Short JWT access lifetime + rotating refresh tokens
- Role-based + object-based authorization
- Rate limit sensitive endpoints (`attempt submit`, `login`)
- Input validation and max payload limits
- Store immutable score audit trail

### 1000+ concurrent users
- Use Redis cache for test metadata and publish state
- paginate all listing endpoints
- DB indexes on attempt/query-heavy fields
- async analytics pre-aggregation (materialized summary tables)
- horizontal app scaling + sticky-free JWT auth

---

## 10. Future Improvements

- Anti-cheat (focus-loss tracking, suspicious patterns)
- Question bank with tags/difficulty and adaptive testing
- Manual review queue for short answers with AI suggestion assist
- Webhook/event bus for real-time teacher dashboards
- Full event sourcing for exam integrity audits
