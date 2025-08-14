
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.conf import settings
from django.db.models import Avg
from schoolapp.models import Student, Course, Task
from testapp.models import TestAttempt


class Performance(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    nazoratishi = models.ForeignKey()
    yakuniy_nazorat = models.DecimalField(max_digits=5, decimal_places=2, default=0)

   

class NazoratIshi(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    # boshqa fieldlar
    status = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

