from django.urls import path

from .views import dashboard

app_name = "blackbook"
urlpatterns = [
    path("", dashboard.dashboard, name="dashboard"),
]