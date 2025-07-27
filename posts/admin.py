from django.contrib import admin
from .models import Post, Comment

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('author', 'content', 'created_at', 'updated_at')
    list_filter = ('author', 'created_at')
    search_fields = ('content', 'author__email')
    date_hierarchy = 'created_at'

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'post', 'content', 'created_at')
    list_filter = ('author', 'created_at')
    search_fields = ('content', 'author__email', 'post__content')
    date_hierarchy = 'created_at'
