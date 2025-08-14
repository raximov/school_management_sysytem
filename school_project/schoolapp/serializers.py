from rest_framework import serializers
from .models import Department, Classroom, Teacher, Student, Course, Enrollment, Task, TaskSubmission

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = '__all__'

class ClassroomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Classroom
        fields = '__all__'

class TeacherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Teacher
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = '__all__'

class EnrollmentSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.name', read_only=True)  # yoki student.name
    course_title = serializers.CharField(source='course.title', read_only=True)

    class Meta:
        model = Enrollment
        fields = ['id', 'student', 'student_name', 'course', 'course_title']

class TaskSerializer(serializers.ModelSerializer):
    student = StudentSerializer()
    course = CourseSerializer()
    class Meta:
        model = Task
        fields = '__all__'


class StudentSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskSubmission
        fields = '__all__'
        read_only_fields = ('student', 'teacher', 'created_at', 'updated_at', 'task', 'score', 'feedback', 'is_done')

class TeacherSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskSubmission
        fields = '__all__'
        read_only_fields = ('student', 'teacher', 'task','created_at', 'updated_at','submitted_file', 'submitted_text')


class StudentTaskStatsSerializer(serializers.ModelSerializer):
    total_tasks = serializers.IntegerField()
    submitted_tasks = serializers.IntegerField()
    completion_rate = serializers.FloatField()
    avg_score = serializers.FloatField()


    class Meta:
        model = Student
        fields = ['id',  'total_tasks', 'submitted_tasks', 'completion_rate', 'avg_score']

