from django.urls import path

from . import views

urlpatterns = [
    path("", views.index),
    path("schedule/", views.examination_schedule),
    path("my-schedule-info/", views.get_my_schedule),
    path("question-paper/", views.question_paper),
]