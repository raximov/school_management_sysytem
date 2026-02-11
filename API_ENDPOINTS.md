# API Endpoints, Swagger, and Requirements

## Swagger / OpenAPI
This project already exposes drf-spectacular endpoints:
- Schema JSON: `/api/schema/`
- Swagger UI: `/api/docs/`
- Redoc UI: `/api/redoc/`

## New V1 Endpoints (testapp)
Base prefix: `/testapp/`

### Student
- `GET /testapp/api/v1/student/tests/`  
  List tests available to logged-in student via enrollments.

- `POST /testapp/api/v1/student/tests/{test_id}/start/`  
  Create/get a test attempt for current student.

- `POST /testapp/api/v1/student/attempts/{attempt_id}/submit/`  
  Submit answers payload and compute score using scoring engine.

- `GET /testapp/api/v1/student/attempts/{attempt_id}/result/`  
  Get attempt result and summary.

### Teacher
- `GET /testapp/api/v1/teacher/tests/{test_id}/results/`  
  Get all attempt results for a teacher-owned test.

## Requirements
Install dependencies from:
- `requirements.txt`

PostgreSQL support is included via:
- `psycopg2-binary`

Environment example:
- `.env.example`
