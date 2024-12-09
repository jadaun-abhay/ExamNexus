from django.urls import path

from . import views

urlpatterns = [
    path("", views.side_bar),
    path("login/", views.login_user),
    path("logout/", views.logout_user),
    path("register/", views.registration),
    path("dropdowns/", views.dropdowns),
    path("get-courses/", views.get_courses_list),
    path("get-genders/", views.get_genders_list),
    path("records/", views.records),
    path("dashboard/", views.dashboard),
    path("exam-types/", views.examination_types),
    path("profile/", views.get_my_profile),
]