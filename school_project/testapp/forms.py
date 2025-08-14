# testapp/forms.py
from django import forms
from .models import Test, Question, Answer

class TestForm(forms.ModelForm):
    class Meta:
        model = Test
        fields = ['title']

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['text', 'question_type', 'mark']

class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ['text', 'is_correct']
