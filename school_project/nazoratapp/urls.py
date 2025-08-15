# urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NazoratViewSet, NazoratResultViewSet, NazoratResultsView, nazorat_table_view

router = DefaultRouter()
router.register(r'nazorats', NazoratViewSet)
router.register(r'nazorat-result', NazoratResultViewSet, basename='nazorat-results')

urlpatterns = [
    path('', include(router.urls)),
    path('nazorat-result-list/', NazoratResultsView.as_view(), name='nazorat-results-list'),
    path('nazorat/<int:nazorat_id>/table/', nazorat_table_view, name='nazorat-table'),
]
