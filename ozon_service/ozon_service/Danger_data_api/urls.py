from rest_framework.routers import DefaultRouter

router = DefaultRouter()
from django.urls import path
from ozon_service.Danger_data_api import views
urlpatterns = [
    path('danger_level_service/', views.GetDangerLevel.as_view())

]

