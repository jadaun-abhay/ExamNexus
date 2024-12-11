from django.urls import path

from . import views

urlpatterns = [
    path("", views.index),
    path("get-exam/", views.examinations),
    path("get-subjects/", views.subjects),
    path("examination/", views.examination)
]
