from django.urls import path
from domain import views

urlpatterns = [
    path("", views.index, name="index"),
    path("results/", views.results, name='results'),
    path("subdomains/", views.get_subdomains, name='subdomains'),
    path("domains/", views.get_search_concepts, name='domains'),
    path("configurations/", views.modify_configurations, name='configurations'),
    path("add_filter/<str:filter_value>/<str:filter_action>/", views.add_filter, name='add_filter'),
]