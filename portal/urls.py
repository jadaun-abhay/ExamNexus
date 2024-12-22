from django.urls import path

from . import views

urlpatterns = [
    #path("left-panel/", views.left_panel),
    path("left-panel/", views.left_panel),
    path("login/", views.login_user),
    path("logout/", views.logout_user),
    path("register/", views.registration),
    path("dropdowns/", views.dropdowns),
    path("dropdowns/customization/", views.dropdowns_customisation),
    path("records/", views.records),
    path("dashboard/", views.dashboard),
    path("exam_pattern/", views.examination_customization),
    path("profile/", views.user_profile),
]