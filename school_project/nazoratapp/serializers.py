# serializers.py
from rest_framework import serializers
from .models import Nazorat, NazoratResult
from schoolapp.models import Student  # Assuming Student model is in schoolapp
from schoolapp.serializers import StudentSerializer  # Adjust import if needed


class NazoratSerializer(serializers.ModelSerializer):
    class Meta:
        model = Nazorat
        fields = '__all__'


class NazoratResultSerializer(serializers.ModelSerializer):
    # Fields from Nazorat (related_name 'nazorat')
    title = serializers.CharField(source='nazorat.title', read_only=True)
    description = serializers.CharField(source='nazorat.description', read_only=True)
    source_type = serializers.CharField(source='nazorat.source_type', read_only=True)
    source_id = serializers.IntegerField(source='nazorat.source_id', read_only=True)
    max_score = serializers.FloatField(source='nazorat.max_score', read_only=True)

    # Related student info
    class Meta:
        model = NazoratResult
        fields = [
            'id',
            'nazorat',
            'title',
            'description',
            'source_type',
            'source_id',
            'max_score',
            'student',
            
            'best_score',
            'attempt_count',
            'last_updated',
        ]

    def get_student_name(self, obj):
        return f"{obj.student.user.first_name} {obj.student.user.last_name}"
