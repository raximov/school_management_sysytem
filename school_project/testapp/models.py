# testapp/models.py
from django.db import models
from schoolapp.models import Teacher, Student,Course

class Test(models.Model):
    title = models.CharField(max_length=255)
    teacherid = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='tests')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Question(models.Model):
    ONE_CHOICE = 'OC'
    MULTIPLE_CHOICE = 'MC'
    ORDERING = 'ORD'
    MATCHING = 'MAT'
    WRITTEN = 'WR' 

    QUESTION_TYPES = [
        (ONE_CHOICE, 'One choice'),
        (MULTIPLE_CHOICE, 'Multiple choice'),
        (ORDERING, 'Ordering'),
        (MATCHING, 'Matching'),
        (WRITTEN, 'Written answer'),
    ]

    testid = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    question_type = models.CharField(max_length=3, choices=QUESTION_TYPES)

    # def __str__(self):
    #     return f"{self.text} ({self.question_type()})"


class Answer(models.Model):
    questionid = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answer_options')
    text = models.TextField()
    is_correct = models.BooleanField(default=False)  # Only for MC and OC

    # For ORDERING or MATCHING questions
    order = models.PositiveIntegerField(null=True, blank=True)     # For ORDERING
    match_text = models.TextField(blank=True, null=True)           # For MATCHING
    mark = models.FloatField(default=1.1)  # Points for this answer
    def __str__(self):
        return self.text


class TestAttempt(models.Model):
    studentid = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='test_attempts')
    testid = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='attempts')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # def __str__(self):
    #     return f"{self.student.user.username} - {self.test.title}"


class StudentAnswer(models.Model):
    attempt = models.ForeignKey(TestAttempt, on_delete=models.CASCADE, related_name='answers')
    questionid = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_answers = models.ManyToManyField(Answer, blank=True)  # For MC/OC
    written_answer = models.TextField(blank=True, null=True)       # For WR
    scored_mark = models.FloatField(default=0.0)  # Points scored for this answer


    def __str__(self):
        return f"Answer to {self.questionid.id} by {self.attempt.studentid.user.username}"

class CourseTest(models.Model):
    testid = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='course_tests')
    courseid = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='course_tests')
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    attemt_count = models.PositiveIntegerField(default=3)  # Number of attempts allowed
    test_attempt_id = models.ForeignKey(TestAttempt, on_delete=models.CASCADE, null=True, blank=True, related_name='course_tests')


    def __str__(self):
        return f"{self.courseid} - {self.test.title}"