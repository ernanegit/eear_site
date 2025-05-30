from django.urls import path
from . import views

app_name = 'materials'

urlpatterns = [
    path('', views.materials_list, name='materials_list'),
    path('download/<int:material_id>/', views.download_material, name='download'),
]