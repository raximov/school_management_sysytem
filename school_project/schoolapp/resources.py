# myapp/resources.py
from import_export import resources
from .models import Student

class StudentResource(resources.ModelResource):
    class Meta:
        model = Student
        fields = (
            'id', 'name', 'middle_name', 'last_name', 'email', 'gender',
             'district', 'region', 'address',
            'profile_photo', 'is_active'
        )


