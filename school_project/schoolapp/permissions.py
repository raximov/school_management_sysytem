from rest_framework.permissions import BasePermission

class IsStudent(BasePermission):
    """
    Allows access only to users with a student_profile.
    """
    def has_permission(self, request, view):
        return hasattr(request.user, 'student_profile')
class IsTeacher(BasePermission):
    """
    Allows access only to users with a teacher_profile.
    """
    def has_permission(self, request, view):
        return hasattr(request.user, 'teacher_profile') 
class IsAuthenticated(BasePermission):
    """
    Allows access only to authenticated users.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
