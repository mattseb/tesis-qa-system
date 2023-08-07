from django.urls import path
from domain import views

urlpatterns = [
    path("", views.index, name="index"),
    path("subdomains/", views.get_subdomains, name='subdomains'),
    path("domains/", views.get_search_concepts, name='domains'),
]