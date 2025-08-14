from rest_framework.permissions import BasePermission, IsAuthenticated

class IsStudent(BasePermission):
    def has_permission(self, request, view):
        return hasattr(request.user, 'student_profile')

class IsTeacher(BasePermission):
    def has_permission(self, request, view):
        return hasattr(request.user, 'teacher_profile')
