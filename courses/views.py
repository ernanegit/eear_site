from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q, Prefetch
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator
from django.core.exceptions import PermissionDenied
import json
import logging

from .models import Subject, Course, Lesson, Progress
from accounts.models import Enrollment

logger = logging.getLogger(__name__)

def home(request):
    """Página inicial com cursos e matérias em destaque"""
    try:
        # Otimizar queries com select_related
        subjects = Subject.objects.filter(is_active=True).prefetch_related(
            Prefetch('courses', queryset=Course.objects.filter(is_active=True))
        )[:6]
        
        featured_courses = Course.objects.filter(
            is_active=True
        ).select_related('subject')[:3]
        
        context = {
            'subjects': subjects,
            'featured_courses': featured_courses,
        }
        return render(request, 'courses/home.html', context)
    except Exception as e:
        logger.error(f"Error in home view: {e}")
        messages.error(request, 'Erro ao carregar a página inicial.')
        return render(request, 'courses/home.html', {'subjects': [], 'featured_courses': []})

@login_required
def dashboard(request):
    """Dashboard do usuário com estatísticas e progresso"""
    try:
        # Estatísticas básicas
        total_courses = Course.objects.filter(is_active=True).count()
        completed_lessons = Progress.objects.filter(
            user=request.user, 
            completed=True
        ).count()
        
        # Cursos em progresso - otimizado
        in_progress_courses = Course.objects.filter(
            lessons__progress__user=request.user,
            lessons__progress__completed=False,
            is_active=True
        ).select_related('subject').distinct()[:3]
        
        # Próximas aulas - otimizado
        next_lessons = Lesson.objects.filter(
            course__in=in_progress_courses
        ).select_related('course', 'course__subject').exclude(
            progress__user=request.user,
            progress__completed=True
        )[:5]
        
        # Calcular progresso geral
        total_lessons_started = Progress.objects.filter(user=request.user).count()
        progress_percentage = (
            (completed_lessons / total_lessons_started * 100) 
            if total_lessons_started > 0 else 0
        )
        
        context = {
            'total_courses': total_courses,
            'completed_lessons': completed_lessons,
            'in_progress_courses': in_progress_courses,
            'next_lessons': next_lessons,
            'progress_percentage': round(progress_percentage, 1),
        }
        return render(request, 'courses/dashboard.html', context)
    
    except Exception as e:
        logger.error(f"Error in dashboard view for user {request.user.id}: {e}")
        messages.error(request, 'Erro ao carregar o dashboard.')
        return render(request, 'courses/dashboard.html', {
            'total_courses': 0,
            'completed_lessons': 0,
            'in_progress_courses': [],
            'next_lessons': [],
            'progress_percentage': 0,
        })

def courses_list(request):
    """Lista de cursos com filtros e paginação"""
    try:
        # Base queryset otimizado
        courses = Course.objects.filter(
            is_active=True
        ).select_related('subject').prefetch_related('lessons')
        
        subjects = Subject.objects.filter(is_active=True)
        
        # Aplicar filtros
        selected_subject = request.GET.get('subject')
        selected_level = request.GET.get('level')
        search = request.GET.get('search')
        
        if selected_subject:
            try:
                selected_subject = int(selected_subject)
                courses = courses.filter(subject_id=selected_subject)
            except (ValueError, TypeError):
                pass
        
        if selected_level and selected_level in [choice[0] for choice in Course.LEVEL_CHOICES]:
            courses = courses.filter(level=selected_level)
        
        if search:
            search = search.strip()
            if search:
                courses = courses.filter(
                    Q(title__icontains=search) | 
                    Q(description__icontains=search) |
                    Q(subject__name__icontains=search)
                )
        
        # Paginação
        paginator = Paginator(courses, 12)
        page_number = request.GET.get('page')
        courses_page = paginator.get_page(page_number)
        
        context = {
            'courses': courses_page,
            'subjects': subjects,
            'selected_subject': selected_subject,
            'selected_level': selected_level,
            'level_choices': Course.LEVEL_CHOICES,
            'search': search,
        }
        return render(request, 'courses/courses_list.html', context)
    
    except Exception as e:
        logger.error(f"Error in courses_list view: {e}")
        messages.error(request, 'Erro ao carregar lista de cursos.')
        return render(request, 'courses/courses_list.html', {
            'courses': [],
            'subjects': [],
            'level_choices': Course.LEVEL_CHOICES,
        })

@login_required
def course_detail(request, course_id):
    """Detalhes do curso com verificação de acesso"""
    try:
        course = get_object_or_404(
            Course.objects.select_related('subject').prefetch_related(
                'lessons__progress'
            ), 
            id=course_id, 
            is_active=True
        )
        
        lessons = course.lessons.all()
        
        # Verificar acesso ao curso
        has_access = True
        if course.is_premium:
            try:
                enrollment = request.user.enrollment
                has_access = (
                    enrollment.status == 'active' and 
                    enrollment.plan in ['premium', 'annual']
                )
            except Enrollment.DoesNotExist:
                has_access = False
        
        # Calcular progresso do usuário
        total_lessons = lessons.count()
        completed_lessons_count = Progress.objects.filter(
            user=request.user,
            lesson__course=course,
            completed=True
        ).count()
        
        progress_percentage = (
            (completed_lessons_count / total_lessons * 100) 
            if total_lessons > 0 else 0
        )
        
        # Marcar aulas como completas para exibição
        user_progress = {}
        if request.user.is_authenticated:
            progress_qs = Progress.objects.filter(
                user=request.user,
                lesson__in=lessons
            ).values('lesson_id', 'completed')
            user_progress = {p['lesson_id']: p['completed'] for p in progress_qs}
        
        context = {
            'course': course,
            'lessons': lessons,
            'has_access': has_access,
            'progress_percentage': round(progress_percentage, 1),
            'completed_lessons': completed_lessons_count,
            'total_lessons': total_lessons,
            'user_progress': user_progress,
        }
        return render(request, 'courses/course_detail.html', context)
    
    except Course.DoesNotExist:
        messages.error(request, 'Curso não encontrado.')
        return redirect('courses:courses_list')
    except Exception as e:
        logger.error(f"Error in course_detail view for course {course_id}: {e}")
        messages.error(request, 'Erro ao carregar detalhes do curso.')
        return redirect('courses:courses_list')

@login_required
def lesson_detail(request, lesson_id):
    """Detalhes da aula com verificação de acesso"""
    try:
        lesson = get_object_or_404(
            Lesson.objects.select_related('course', 'course__subject'),
            id=lesson_id
        )
        course = lesson.course
        
        # Verificar acesso à aula
        has_access = lesson.is_free
        if not has_access and course.is_premium:
            try:
                enrollment = request.user.enrollment
                has_access = (
                    enrollment.status == 'active' and 
                    enrollment.plan in ['premium', 'annual']
                )
            except Enrollment.DoesNotExist:
                has_access = False
        
        if not has_access:
            messages.error(
                request, 
                'Você precisa de uma assinatura premium para acessar esta aula.'
            )
            return redirect('courses:course_detail', course_id=course.id)
        
        # Obter ou criar progresso
        progress, created = Progress.objects.get_or_create(
            user=request.user,
            lesson=lesson,
            defaults={'completed': False}
        )
        
        # Navegação entre aulas
        next_lesson = course.lessons.filter(order__gt=lesson.order).first()
        prev_lesson = course.lessons.filter(order__lt=lesson.order).last()
        
        # Progresso geral do curso
        course_progress = calculate_course_progress(request.user, course)
        
        context = {
            'lesson': lesson,
            'course': course,
            'progress': progress,
            'next_lesson': next_lesson,
            'prev_lesson': prev_lesson,
            'course_progress': course_progress,
        }
        return render(request, 'courses/lesson_detail.html', context)
    
    except Lesson.DoesNotExist:
        messages.error(request, 'Aula não encontrada.')
        return redirect('courses:courses_list')
    except Exception as e:
        logger.error(f"Error in lesson_detail view for lesson {lesson_id}: {e}")
        messages.error(request, 'Erro ao carregar a aula.')
        return redirect('courses:courses_list')

@login_required
@require_http_methods(["POST"])
@csrf_protect
def mark_lesson_complete(request, lesson_id):
    """Marcar aula como completa via AJAX"""
    try:
        lesson = get_object_or_404(Lesson, id=lesson_id)
        
        # Verificar se usuário tem acesso
        if not lesson.is_free and lesson.course.is_premium:
            try:
                enrollment = request.user.enrollment
                has_access = (
                    enrollment.status == 'active' and 
                    enrollment.plan in ['premium', 'annual']
                )
                if not has_access:
                    raise PermissionDenied()
            except Enrollment.DoesNotExist:
                raise PermissionDenied()
        
        # Atualizar progresso
        progress, created = Progress.objects.get_or_create(
            user=request.user,
            lesson=lesson
        )
        
        if not progress.completed:
            progress.completed = True
            progress.save()
            
            logger.info(f"User {request.user.id} completed lesson {lesson_id}")
            
            return JsonResponse({
                'success': True,
                'message': 'Aula marcada como concluída!'
            })
        else:
            return JsonResponse({
                'success': True,
                'message': 'Aula já estava concluída.'
            })
    
    except PermissionDenied:
        return JsonResponse({
            'success': False,
            'message': 'Você não tem permissão para acessar esta aula.'
        }, status=403)
    except Lesson.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Aula não encontrada.'
        }, status=404)
    except Exception as e:
        logger.error(f"Error marking lesson {lesson_id} complete for user {request.user.id}: {e}")
        return JsonResponse({
            'success': False,
            'message': 'Erro interno. Tente novamente.'
        }, status=500)

@login_required
@require_http_methods(["POST"])
@csrf_protect
def update_lesson_progress(request, lesson_id):
    """Atualizar tempo assistido da aula via AJAX"""
    try:
        lesson = get_object_or_404(Lesson, id=lesson_id)
        
        # Parse JSON data
        data = json.loads(request.body)
        watch_time = data.get('watch_time', 0)
        
        if not isinstance(watch_time, (int, float)) or watch_time < 0:
            return JsonResponse({
                'success': False,
                'message': 'Tempo inválido.'
            }, status=400)
        
        # Atualizar progresso
        progress, created = Progress.objects.get_or_create(
            user=request.user,
            lesson=lesson
        )
        
        progress.watch_time = max(progress.watch_time, int(watch_time))
        progress.save()
        
        return JsonResponse({'success': True})
    
    except (json.JSONDecodeError, KeyError):
        return JsonResponse({
            'success': False,
            'message': 'Dados inválidos.'
        }, status=400)
    except Exception as e:
        logger.error(f"Error updating progress for lesson {lesson_id}: {e}")
        return JsonResponse({
            'success': False,
            'message': 'Erro interno.'
        }, status=500)

def calculate_course_progress(user, course):
    """Calcular progresso do usuário no curso"""
    try:
        total_lessons = course.lessons.count()
        if total_lessons == 0:
            return {'percentage': 0, 'completed': 0, 'total': 0}
        
        completed_count = Progress.objects.filter(
            user=user,
            lesson__course=course,
            completed=True
        ).count()
        
        percentage = (completed_count / total_lessons) * 100
        
        return {
            'percentage': round(percentage, 1),
            'completed': completed_count,
            'total': total_lessons
        }
    except Exception as e:
        logger.error(f"Error calculating progress for user {user.id} in course {course.id}: {e}")
        return {'percentage': 0, 'completed': 0, 'total': 0}