# views.py
from rest_framework import viewsets, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import render, get_object_or_404
from django.db.models import Max
from .models import Nazorat, NazoratResult
from .serializers import NazoratSerializer, NazoratResultSerializer
from testapp.models import TestAttempt
from schoolapp.models import TaskSubmission


class NazoratViewSet(viewsets.ModelViewSet):
    queryset = Nazorat.objects.all()
    serializer_class = NazoratSerializer

    @action(detail=True, methods=['post'])
    def calculate_scores(self, request, pk=None):
        nazorat = self.get_object()

        if nazorat.source_type == 'task':
            submissions = TaskSubmission.objects.filter(task=nazorat.source)
            students = submissions.values_list('student', flat=True).distinct()

            for student in students:
                student_subs = submissions.filter(student=student)
                best_score = student_subs.aggregate(Max('score'))['score__max'] or 0
                attempt_count = student_subs.count()

                NazoratResult.objects.update_or_create(
                    nazorat=nazorat,
                    student=student,
                    defaults={
                        'best_score': best_score,
                        'attempt_count': attempt_count
                    }
                )

        elif nazorat.source_type == 'test':
            attempts = TestAttempt.objects.filter(test=nazorat.source)
            students = attempts.values_list('student', flat=True).distinct()

            for student in students:
                student_attempts = attempts.filter(student=student)
                best_score = student_attempts.aggregate(Max('score'))['score__max'] or 0
                attempt_count = student_attempts.count()

                NazoratResult.objects.update_or_create(
                    nazorat=nazorat,
                    student=student,
                    defaults={
                        'best_score': best_score,
                        'attempt_count': attempt_count
                    }
                )

        return Response({"status": "Scores updated"})


class NazoratResultViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = NazoratResult.objects.select_related('nazorat', 'student')
    serializer_class = NazoratResultSerializer


class NazoratResultsView(generics.ListAPIView):
    queryset = NazoratResult.objects.select_related('nazorat', 'student')
    serializer_class = NazoratResultSerializer


def nazorat_table_view(request, nazorat):
    nazorat = get_object_or_404(Nazorat, id=nazorat)
    results = NazoratResult.objects.filter(nazorat=nazorat).select_related('student')
    return render(request, 'nazorat_table.html', {
        'nazorat': nazorat,
        'results': results
    })
