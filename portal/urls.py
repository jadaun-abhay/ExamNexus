from django.urls import path

from . import views

urlpatterns = [
    path("", views.index),
    path("login/", views.login_user),
    path("logout/", views.logout_user),
    path("register/", views.registration),
    path("dropdowns/", views.dropdowns),
    path("get-courses/", views.get_courses_list),
    path("get-genders/", views.get_genders_list),
    path("records/", views.records),
    path("dashboard/", views.dashboard),
]