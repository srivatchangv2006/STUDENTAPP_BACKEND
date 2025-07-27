from django.contrib import admin
from .models import Story, Quiz, Question, QuizAttempt, Answer

@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('title', 'user__username', 'user__email')
    date_hierarchy = 'created_at'

@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('story', 'title', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('title', 'story__title')
    date_hierarchy = 'created_at'

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('quiz', 'question_text', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('question_text', 'quiz__title')
    date_hierarchy = 'created_at'

@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'quiz', 'score', 'completed', 'started_at', 'completed_at')
    list_filter = ('completed', 'started_at', 'completed_at')
    search_fields = ('user__username', 'user__email', 'quiz__title')
    date_hierarchy = 'started_at'

@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('attempt', 'question', 'is_correct', 'answered_at')
    list_filter = ('is_correct', 'answered_at')
    search_fields = ('attempt__user__username', 'question__question_text')
    date_hierarchy = 'answered_at'
