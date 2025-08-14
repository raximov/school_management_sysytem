from django.contrib import admin
from .models import Test, Question, Answer, TestAttempt, StudentAnswer, EnrollmentTest

# Register your models here.
admin.site.register([ Test, Question, Answer, TestAttempt, StudentAnswer, EnrollmentTest])
