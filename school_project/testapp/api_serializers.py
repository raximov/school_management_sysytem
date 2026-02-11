from rest_framework import serializers


class AttemptAnswerInputSerializer(serializers.Serializer):
    question_id = serializers.IntegerField()
    selected_option_ids = serializers.ListField(
        child=serializers.IntegerField(), required=False, allow_empty=True
    )
    written_answer = serializers.CharField(required=False, allow_blank=True)


class AttemptSubmitInputSerializer(serializers.Serializer):
    answers = AttemptAnswerInputSerializer(many=True)


class AttemptResultOutputSerializer(serializers.Serializer):
    attempt_id = serializers.IntegerField()
    score = serializers.FloatField()
    percentage = serializers.FloatField()
    total_questions = serializers.IntegerField()
    total_answers = serializers.IntegerField()
