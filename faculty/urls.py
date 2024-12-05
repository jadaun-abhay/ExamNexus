from django.urls import path

from . import views

urlpatterns = [
    path("", views.index),
    path("create-schedule/", views.schedule),
]