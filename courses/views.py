from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.http import JsonResponse
from django.core.paginator import Paginator
from .models import Subject, Course, Lesson, Progress, Quiz, Question
from accounts.models import Enrollment

def home(request):
    subjects = Subject.objects.filter(is_active=True)[:6]
    featured_courses = Course.objects.filter(is_active=True)[:3]
    
    context = {
        'subjects': subjects,
        'featured_courses': featured_courses,
    }
    return render(request, 'courses/home.html', context)

@login_required
def dashboard(request):
    # Estatísticas do usuário
    total_courses = Course.objects.filter(is_active=True).count()
    completed_lessons = Progress.objects.filter(user=request.user, completed=True).count()
    
    # Cursos em progresso
    in_progress_courses = Course.objects.filter(
        lessons__progress__user=request.user,
        lessons__progress__completed=False
    ).distinct()[:3]
    
    # Próximas aulas
    next_lessons = Lesson.objects.filter(
        course__in=in_progress_courses
    ).exclude(
        progress__user=request.user,
        progress__completed=True
    )[:5]
    
    context = {
        'total_courses': total_courses,
        'completed_lessons': completed_lessons,
        'in_progress_courses': in_progress_courses,
        'next_lessons': next_lessons,
    }
    return render(request, 'courses/dashboard.html', context)

def courses_list(request):
    subjects = Subject.objects.filter(is_active=True)
    courses = Course.objects.filter(is_active=True)
    
    # Filters
    selected_subject = request.GET.get('subject')
    selected_level = request.GET.get('level')
    search = request.GET.get('search')
    
    if selected_subject:
        courses = courses.filter(subject_id=selected_subject)
    
    if selected_level:
        courses = courses.filter(level=selected_level)
    
    if search:
        courses = courses.filter(
            Q(title__icontains=search) | 
            Q(description__icontains=search)
        )
    
    # Pagination
    paginator = Paginator(courses, 12)
    page_number = request.GET.get('page')
    courses = paginator.get_page(page_number)
    
    context = {
        'courses': courses,
        'subjects': subjects,
        'selected_subject': selected_subject,
        'selected_level': selected_level,
        'level_choices': Course.LEVEL_CHOICES,
        'search': search,
    }
    return render(request, 'courses/courses_list.html', context)

@login_required
def course_detail(request, course_id):
    course = get_object_or_404(Course, id=course_id, is_active=True)
    lessons = course.lessons.all()
    
    # Verificar se o usuário tem acesso ao curso
    has_access = True
    if course.is_premium:
        try:
            enrollment = request.user.enrollment
            has_access = enrollment.status == 'active' and enrollment.plan in ['premium', 'annual']
        except Enrollment.DoesNotExist:
            has_access = False
    
    # Progresso do usuário no curso
    total_lessons = lessons.count()
    completed_lessons = Progress.objects.filter(
        user=request.user,
        lesson__course=course,
        completed=True
    ).count()
    
    progress_percentage = (completed_lessons / total_lessons * 100) if total_lessons > 0 else 0
    
    context = {
        'course': course,
        'lessons': lessons,
        'has_access': has_access,
        'progress_percentage': progress_percentage,
        'completed_lessons': completed_lessons,
        'total_lessons': total_lessons,
    }
    return render(request, 'courses/course_detail.html', context)

@login_required
def lesson_detail(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    course = lesson.course
    
    # Verificar acesso
    has_access = lesson.is_free
    if not has_access and course.is_premium:
        try:
            enrollment = request.user.enrollment
            has_access = enrollment.status == 'active' and enrollment.plan in ['premium', 'annual']
        except Enrollment.DoesNotExist:
            has_access = False
    
    if not has_access:
        messages.error(request, 'Você precisa de uma assinatura premium para acessar esta aula.')
        return redirect('courses:course_detail', course_id=course.id)
    
    # Obter ou criar progresso
    progress, created = Progress.objects.get_or_create(
        user=request.user,
        lesson=lesson,
        defaults={'completed': False}
    )
    
    # Próxima e anterior aula
    next_lesson = lesson.course.lessons.filter(order__gt=lesson.order).first()
    prev_lesson = lesson.course.lessons.filter(order__lt=lesson.order).last()
    
    context = {
        'lesson': lesson,
        'course': course,
        'progress': progress,
        'next_lesson': next_lesson,
        'prev_lesson': prev_lesson,
    }
    return render(request, 'courses/lesson_detail.html', context)

@login_required
def mark_lesson_complete(request, lesson_id):
    if request.method == 'POST':
        lesson = get_object_or_404(Lesson, id=lesson_id)
        progress, created = Progress.objects.get_or_create(
            user=request.user,
            lesson=lesson
        )
        
        progress.completed = True
        progress.save()
        
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False})