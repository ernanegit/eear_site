from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('list/', views.courses_list, name='courses_list'),
    path('<int:course_id>/', views.course_detail, name='course_detail'),
    path('lesson/<int:lesson_id>/', views.lesson_detail, name='lesson_detail'),
    path('lesson/<int:lesson_id>/complete/', views.mark_lesson_complete, name='mark_complete'),
    # Nova URL para atualizar progresso de vídeo
    path('lesson/<int:lesson_id>/update-progress/', views.update_lesson_progress, name='update_progress'),
]