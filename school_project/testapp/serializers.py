from rest_framework import serializers
from .models import Test, Question, Answer, StudentAnswer, TestAttempt


class AnswerOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = "__all__"

class QuestionSerializer(serializers.ModelSerializer):
    answer_options = AnswerOptionSerializer(many=True)

    class Meta:
        model = Question
        fields = "__all__"#['id', 'text', 'question_type', 'answers']

    def get_answers(self, obj):
        return AnswerOptionSerializer(obj.answers.all(), many=True).data
    


class TestSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True)

    class Meta:
        model = Test
        fields = "__all__"

    def create(self, validated_data):
        questions_data = validated_data.pop('questions')
        test = Test.objects.create(**validated_data)

        for q_data in questions_data:
            answers_data = q_data.pop('answer_options')
            question = Question.objects.create(testid=test, **q_data)

            for a_data in answers_data:
                Answer.objects.create(questionid=question, **a_data)

        return test
    def update(self, instance, validated_data):
        questions_data = validated_data.pop('questions', None)

        instance.title = validated_data.get('title', instance.title)
        instance.teacherid = validated_data.get('teacherid', instance.teacherid)
        instance.save()

        if questions_data is not None:
            instance.questions.all().delete()

            for question_data in questions_data:
                answer_options_data = question_data.pop('answer_options', [])
                question_data.pop('testid', None)  # ✅ MUHIM
                question = Question.objects.create(testid=instance, **question_data)

                for answer_data in answer_options_data:
                    answer_data.pop('questionid', None)  # ✅ Shuningdek, kerak bo‘lsa bu ham
                    Answer.objects.create(questionid=question, **answer_data)

        return instance


class StudentAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentAnswer
        fields = '__all__'

class TestAttemptSerializer(serializers.ModelSerializer):
    answers = StudentAnswerSerializer(many=True, read_only=True)

    class Meta:
        model = TestAttempt
        fields = "__all__" # ['id', 'studentid', 'testid', 'started_at', 'answers']

class TestAttemptResultSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.user.get_full_name", read_only=True)
    answers = StudentAnswerSerializer(many=True, read_only=True)

    class Meta:
        model = TestAttempt
        fields = "__all__" #['id', 'student_name', 'score', 'submitted_at', 'answers']
