from django.urls import path
from . import views

urlpatterns = [
    path("", views.hero_list, name="hero_list"),
    path("<str:hero_id>/", views.hero_detail, name="hero_detail"),
]
