from django.db import models
from schoolapp.models import Teacher, Student, Enrollment, Course

class Test(models.Model):
    title = models.CharField(max_length=255)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='tests')
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

    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    question_type = models.CharField(max_length=3, choices=QUESTION_TYPES)
    mark = models.FloatField(default=1.1)

    def __str__(self):
        return self.text


class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answer_options')
    text = models.TextField()
    is_correct = models.BooleanField(default=False)

    # For ORDERING or MATCHING questions
    order = models.PositiveIntegerField(null=True, blank=True)
    match_text = models.TextField(blank=True, null=True)
    

    def __str__(self):
        return self.text


class TestAttempt(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='test_attempts')
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='attempts')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.student.user.username} - {self.test.title}"

class TestAttempt(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    test = models.ForeignKey(Test, on_delete=models.CASCADE)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    score = models.FloatField(default=0)
    percentage = models.FloatField(default=0)

    def __str__(self):
        return f"{self.student} - {self.test}"


class AnswerSelection(models.Model):
    attempt = models.ForeignKey(TestAttempt, on_delete=models.CASCADE, related_name='selections')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_answer = models.ForeignKey(Answer, on_delete=models.CASCADE, null=True, blank=True)

    def is_correct(self):
        return self.selected_answer and self.selected_answer.is_correct


class StudentAnswer(models.Model):
    attempt = models.ForeignKey(TestAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_answers = models.ManyToManyField(Answer, blank=True)
    written_answer = models.TextField(blank=True, null=True)
    scored_mark = models.FloatField(default=0.0)

    def __str__(self):
        return f"Answer to Q{self.question.id} by {self.attempt.student.user.username}"


class EnrollmentTest(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='enrollment_tests')
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='enrollment_tests')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollment_tests')
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    attempt_count = models.PositiveIntegerField(default=3)

    def __str__(self):
        return f"{self.course} - {self.test.title}"
