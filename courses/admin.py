
# Register your models here.
from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count
from .models import Subject, Course, Lesson, Progress, Quiz, Question, Answer

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'order', 'courses_count', 'is_active']
    list_editable = ['order', 'is_active']
    search_fields = ['name', 'description']
    ordering = ['order', 'name']
    list_per_page = 20
    
    def courses_count(self, obj):
        count = obj.courses.count()
        return format_html('<strong>{}</strong> cursos', count)
    courses_count.short_description = 'Cursos'

class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 1
    fields = ['title', 'lesson_type', 'duration_minutes', 'order', 'is_free']
    ordering = ['order']

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['title', 'subject', 'level_display', 'duration_hours', 'lessons_count', 'is_premium_display', 'is_active', 'created_at']
    list_filter = ['subject', 'level', 'is_premium', 'is_active', 'created_at']
    search_fields = ['title', 'description']
    inlines = [LessonInline]
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    list_per_page = 20
    
    readonly_fields = ['created_at']
    
    def level_display(self, obj):
        colors = {
            'basic': '#28a745',
            'intermediate': '#ffc107',
            'advanced': '#dc3545'
        }
        color = colors.get(obj.level, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_level_display()
        )
    level_display.short_description = 'Nível'
    
    def is_premium_display(self, obj):
        if obj.is_premium:
            return format_html('<span style="color: #ffc107; font-weight: bold;">★ Premium</span>')
        return format_html('<span style="color: #28a745;">Grátis</span>')
    is_premium_display.short_description = 'Acesso'
    
    def lessons_count(self, obj):
        count = obj.lessons.count()
        return format_html('<strong>{}</strong> aulas', count)
    lessons_count.short_description = 'Aulas'

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'lesson_type_display', 'duration_minutes', 'order', 'is_free_display']
    list_filter = ['lesson_type', 'is_free', 'course__subject', 'course']
    search_fields = ['title', 'course__title', 'description']
    ordering = ['course', 'order']
    list_per_page = 30
    
    def lesson_type_display(self, obj):
        icons = {
            'video': '📹',
            'text': '📄',
            'quiz': '❓',
            'exercise': '✏️'
        }
        icon = icons.get(obj.lesson_type, '📄')
        return format_html('{} {}', icon, obj.get_lesson_type_display())
    lesson_type_display.short_description = 'Tipo'
    
    def is_free_display(self, obj):
        if obj.is_free:
            return format_html('<span style="color: #28a745; font-weight: bold;">✓ Grátis</span>')
        return format_html('<span style="color: #dc3545;">🔒 Premium</span>')
    is_free_display.short_description = 'Acesso'

@admin.register(Progress)
class ProgressAdmin(admin.ModelAdmin):
    list_display = ['user', 'lesson', 'course_name', 'completed_display', 'completed_at', 'watch_time_display']
    list_filter = ['completed', 'completed_at', 'lesson__course__subject']
    search_fields = ['user__email', 'user__username', 'lesson__title', 'lesson__course__title']
    date_hierarchy = 'completed_at'
    ordering = ['-completed_at']
    list_per_page = 50
    
    def course_name(self, obj):
        return obj.lesson.course.title
    course_name.short_description = 'Curso'
    
    def completed_display(self, obj):
        if obj.completed:
            return format_html('<span style="color: #28a745; font-weight: bold;">✓ Concluída</span>')
        return format_html('<span style="color: #ffc107;">⏳ Em andamento</span>')
    completed_display.short_description = 'Status'
    
    def watch_time_display(self, obj):
        minutes = obj.watch_time // 60
        return f"{minutes} min"
    watch_time_display.short_description = 'Tempo Assistido'

class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 4
    fields = ['text', 'is_correct', 'order']
    ordering = ['order']

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['text_preview', 'quiz', 'question_type_display', 'order']
    list_filter = ['question_type', 'quiz__lesson__course']
    search_fields = ['text', 'quiz__title']
    inlines = [AnswerInline]
    ordering = ['quiz', 'order']
    list_per_page = 20
    
    def text_preview(self, obj):
        return obj.text[:100] + "..." if len(obj.text) > 100 else obj.text
    text_preview.short_description = 'Pergunta'
    
    def question_type_display(self, obj):
        icons = {
            'multiple': '☑️',
            'true_false': '✅',
            'essay': '📝'
        }
        icon = icons.get(obj.question_type, '☑️')
        return format_html('{} {}', icon, obj.get_question_type_display())
    question_type_display.short_description = 'Tipo'

@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ['title', 'lesson', 'questions_count', 'passing_score']
    list_filter = ['lesson__course__subject', 'passing_score']
    search_fields = ['title', 'lesson__title']
    
    def questions_count(self, obj):
        count = obj.questions.count()
        return format_html('<strong>{}</strong> questões', count)
    questions_count.short_description = 'Questões'