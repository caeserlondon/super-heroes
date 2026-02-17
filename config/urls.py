"""
URL configuration for Super Heroes project.
"""
from django.urls import path, include

urlpatterns = [
    path("", include("heroes.urls")),
]
