from django.urls import path
from questions import views

urlpatterns = [
    path("", views.primero, name="index"),
]