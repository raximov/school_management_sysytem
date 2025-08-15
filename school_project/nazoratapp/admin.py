from django.contrib import admin
from .models import Nazorat, NazoratResult

# Register your models here.
admin.site.register([Nazorat, NazoratResult])