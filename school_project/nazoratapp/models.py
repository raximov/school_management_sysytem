from django.db import models
from schoolapp.models import Course, Student, Task
from testapp.models import Test  # adjust imports

class Nazorat(models.Model):
    SOURCE_TYPE_CHOICES = [
        ('task', 'Task'),
        ('test', 'Test'),
    ]

    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    source_type = models.CharField(max_length=10, choices=SOURCE_TYPE_CHOICES)
    source_id = models.PositiveIntegerField()  # task_id or test_id
    max_score = models.FloatField(default=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.source_type})"


class NazoratResult(models.Model):
    nazorat = models.ForeignKey(Nazorat, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    best_score = models.FloatField(default=0)
    attempt_count = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('nazorat', 'student')

    def __str__(self):
        return f"{self.student} - {self.nazorat} ({self.best_score})"




