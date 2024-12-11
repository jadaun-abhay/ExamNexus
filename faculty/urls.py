from django.urls import path

from . import views

urlpatterns = [
    path("", views.index),
    path("coe/schedule/", views.examination_schedule__coe),
    path("schedule/", views.schedule__faculty),
    path("examination-paper/", views.examination_paper__faculty),
    path("hod/examination-paper/", views.examination_paper__hod),
    path("get-years/", views.years_list),
]
