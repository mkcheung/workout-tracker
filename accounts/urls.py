from django.urls import path, include
from . import views

app_name = "accounts_me"

urlpatterns = [
    path("me/", views.me, name="me"),
]