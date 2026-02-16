from rest_framework import serializers
from .models import Test, Question, Answer, StudentAnswer, TestAttempt, EnrollmentTest
from schoolapp.serializers import CourseSerializer
from schoolapp.models import Course

class TestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Test
        fields = [
            'id',
            'title',
            'description',
            'status',
            'time_limit_sec',
            'passing_percent',
            'teacher',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['teacher', 'created_at', 'updated_at']

class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ['id', 'text', 'question_type', 'mark', 'test']

class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ['id', 'text', 'is_correct', 'question']


class EnrollmentTestSerializer(serializers.ModelSerializer):
    # GET uchun nested
    course = CourseSerializer(read_only=True)
    test = TestSerializer(read_only=True)
    teacher_id = serializers.IntegerField(source='teacher_id', read_only=True)

    # POST/PUT uchun id
    course_id = serializers.PrimaryKeyRelatedField(
        queryset=Course.objects.all(), write_only=True, source='course', required=False
    )
    test_id = serializers.PrimaryKeyRelatedField(
        queryset=Test.objects.all(), write_only=True, source='test', required=False
    )

    class Meta:
        model = EnrollmentTest
        fields = [
            'id', 'course', 'test',
            'course_id', 'test_id',
            'start_date', 'end_date', 'attempt_count', 'teacher_id'
        ]

    def to_internal_value(self, data):
        """
        Accept both payload variants:
        - {"course_id": 1, "test_id": 2}
        - {"course": 1, "test": 2}
        """
        if isinstance(data, dict):
            mutable = dict(data)

            course_value = mutable.get('course')
            if 'course_id' not in mutable and course_value is not None and not isinstance(course_value, dict):
                mutable['course_id'] = course_value

            test_value = mutable.get('test')
            if 'test_id' not in mutable and test_value is not None and not isinstance(test_value, dict):
                mutable['test_id'] = test_value

            data = mutable

        return super().to_internal_value(data)

class StudentAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentAnswer
        fields = '__all__'

class TestAttemptSerializer(serializers.ModelSerializer):
    test = TestSerializer(source='test', read_only=True)
    answers = StudentAnswerSerializer(many=True, read_only=True)

    class Meta:
        model = TestAttempt
        fields = ['id', 'answers', 'started_at', 'completed_at', 'studentid', 'test', 'test']


class TestAttemptResultSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.user.get_full_name", read_only=True)
    answers = StudentAnswerSerializer(many=True, read_only=True)

    class Meta:
        model = TestAttempt
        fields = ['id', 'student_name', 'score', 'submitted_at', 'answers']
