# School Management System Repository Analysis

## What this project is for
This repository contains a **Django-based school management backend + server-rendered UI** for three main domains:

1. **School operations** (`schoolapp`): teachers, students, courses, enrollment, and task submissions.
2. **Testing/exams** (`testapp`): test creation, question/answer authoring, student attempts, and test assignment per course.
3. **Nazorat (control/assessment aggregation)** (`nazoratapp`): stores combined scoring definitions/results sourced from tasks or tests.

The project uses Django REST Framework for API-style endpoints and also serves HTML templates for teacher/student pages.

## High-level architecture

- Project module: `school_project`
- Apps:
  - `schoolapp` (core domain)
  - `testapp` (assessment engine)
  - `nazoratapp` (aggregated control scores)
- Database: SQLite (`db.sqlite3`)
- Media uploads: task files, submissions, student photos under `media/`

## Configuration behavior

`settings.py` shows:
- Installed DRF, CORS, JWT/token/docs-related packages.
- Global DRF defaults require authenticated users (`IsAuthenticated`) with session auth.
- CORS is effectively open in development (`CORS_ALLOW_ALL_ORIGINS = True`).
- API schema/docs enabled through drf-spectacular.

## Routing map (entry points)

Top-level routes in `school_project/urls.py`:
- `/school/` -> `schoolapp.urls`
- `/testapp/` -> `testapp.urls`
- `/nazorat/` -> `nazoratapp.urls`
- `/api/schema`, `/api/docs`, `/api/redoc` for API documentation.

## Core domain model walkthrough

### 1) schoolapp (core school workflows)
Main models:
- `Department`, `Classroom`
- `Teacher` (linked 1:1 with Django `User`)
- `Student` (linked 1:1 with Django `User` + extensive demographic fields)
- `Course` (teacher/department/classroom + JSON schedule)
- `Enrollment` (student-course many-to-many through model)
- `Task` (teacher creates course task)
- `TaskSubmission` (student submission with score/feedback)

Primary workflow:
1. Register/login as teacher/student.
2. Enroll students into courses.
3. Teacher creates tasks for a course.
4. Student submits files/text for tasks.
5. Teacher reviews submissions and sets score/feedback.

### 2) testapp (tests/quizzes)
Main models:
- `Test` created by teacher.
- `Question` with different types (single choice, multiple, ordering, matching, written).
- `Answer` choices per question.
- `EnrollmentTest` links a test to a course and timing/attempt limits.
- `TestAttempt` and `StudentAnswer` track student attempts and responses.

Primary workflow:
1. Teacher creates tests, questions, answer options.
2. Teacher assigns test to a course (`EnrollmentTest`).
3. Student sees assigned tests and submits answers.
4. Results/attempt details rendered for student/teacher.

### 3) nazoratapp (aggregated evaluation)
Main models:
- `Nazorat`: assessment record pointing to a source type (`task` or `test`) and source id.
- `NazoratResult`: per-student best score and attempt count for that nazorat.

Primary intent:
- Compute per-student best performance from either task submissions or test attempts, and store summarized results.

## How the system works in practice

- **Identity model**: Django `User` is the auth identity, while `Teacher`/`Student` are profile/domain entities.
- **Dual API style**:
  - DRF viewsets/APIViews for CRUD and JSON APIs.
  - Django template views for browser pages (teacher panel, student tests/tasks).
- **Data flow between apps**:
  - `testapp` depends on `schoolapp` models (`Teacher`, `Student`, `Course`, etc.).
  - `nazoratapp` depends on both `schoolapp` (`TaskSubmission`) and `testapp` (`TestAttempt`).

## Notable implementation observations

1. `testapp/models.py` defines `TestAttempt` **twice** (same class name), which can create confusion/maintenance risk.
2. In `nazoratapp/views.py`, score calculation uses `nazorat.source`, but `Nazorat` model has `source_type` + `source_id` fields (no `source` FK/property). This likely breaks `calculate_scores` unless a missing property exists elsewhere.
3. Several URL/view imports include duplication and mixed API/HTML concerns, indicating the project is functional but still in active refactor/iteration.

## Quick startup expectation

Typical local run (assuming dependencies are installed):
1. `python manage.py migrate`
2. `python manage.py createsuperuser`
3. `python manage.py runserver`

Then use:
- `/api/docs/` for API exploration
- `/school/login/` for auth entry (route naming varies by templates/views)
- `/testapp/teacher-panel/` for test management UI

## Current environment check result

`python manage.py check` could not be executed in this environment because Django is not installed in the active Python interpreter.
