from django.contrib import admin
from django.urls import path, include
from ozon_service.Danger_data_api import views
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('ozon_service.Danger_data_api.urls'))

]
