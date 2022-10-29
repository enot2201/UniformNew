from django.urls import path
from . import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
urlpatterns = [
                  path('custom_user/', views.CustomUserViewSet.as_view({'get': 'list', 'post': 'create'})),
                  path('custom_user/detail/', views.UserDetailView.as_view({'get': 'list'})),
                  path('custom_user/<str:pk>/',
                       views.CustomUserViewSet.as_view(
                           {'get': 'retrieve', 'patch': 'partial_update', 'delete': 'destroy'})),
                  path('custom_user/', views.CustomUserViewSet.as_view({'get': 'list', 'post': 'create'})),
                  path('custom_user/<str:pk>/',
                       views.CustomUserViewSet.as_view(
                           {'get': 'retrieve', 'patch': 'partial_update', 'delete': 'destroy'})),
                  path("builder/", views.UserBuilderApiView.as_view()),

              ] + router.urls
