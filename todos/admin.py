from django.contrib import admin

from .models import Category, Tag, Todo


@admin.register(Todo)
class TodoAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "priority", "due_date", "completed", "is_deleted")
    list_filter = ("priority", "completed", "is_deleted", "recurrence")
    search_fields = ("title", "description")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "user")
    search_fields = ("name",)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "user")
    search_fields = ("name",)
