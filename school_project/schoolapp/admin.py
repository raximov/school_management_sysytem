from django.contrib import admin
from .models import Department, Classroom, Teacher, Student, Course, Enrollment, Task, TaskSubmission
from django.utils.html import format_html
from django import forms
from import_export.admin import ImportExportModelAdmin
from .resources import StudentResource



class StudentAdminForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['profile_photo'].required = True

class TeacherAdminForm(forms.ModelForm):
    class Meta:
        model = Teacher
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['profile_photo'].required = True

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    form = TeacherAdminForm
    list_display = ('name', 'last_name', 'email', 'is_active', 'profile_photo_preview')
    readonly_fields = ('profile_photo_preview', 'created_at', 'updated_at')
    fields = (
        'name', 'middle_name', 'last_name', 'email', 'phone',
        'specialization', 'department', 'profile_photo',
        'profile_photo_preview', 'is_active', 'created_at', 'updated_at'
    )

    def profile_photo_preview(self, obj):
        if obj.profile_photo:
            return format_html('<img src="{}" style="height:300px;" />', obj.profile_photo.url)
        return "-"
    profile_photo_preview.short_description = "Profile Photo Preview"

@admin.register(Student)
class StudentAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    resource_class = StudentResource
    form = StudentAdminForm
    list_display = ('name', 'middle_name', 'last_name', 'email', 'is_active', 'profile_photo_preview')
    readonly_fields = ('created_at', 'updated_at', 'profile_photo_preview')
    fields = (
        'name', 'middle_name', 'last_name', 'email', 'gender',
        'date_of_birth', 'district', 'region', 'address',
        'profile_photo', 'profile_photo_preview', 'is_active',
        'created_at', 'updated_at'
    )

    def profile_photo_preview(self, obj):
        if obj.profile_photo:
            return format_html('<img src="{}" style="height:300px;" />', obj.profile_photo.url)
        return "-"
    profile_photo_preview.short_description = "Profile Photo Preview"

admin.site.register(Department)
admin.site.register(Classroom)
admin.site.register(Course)
admin.site.register(Enrollment)
admin.site.register(TaskSubmission)
admin.site.register(Task)




