from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path("", views.TodoListView.as_view(), name="todo_list"),
    path("create/", views.TodoCreateView.as_view(), name="todo_create"),
    path("edit/<int:pk>/", views.TodoUpdateView.as_view(), name="todo_edit"),
    path("delete/<int:pk>/", views.TodoDeleteView.as_view(), name="todo_delete"),
    path("toggle/<int:pk>/", views.toggle_todo, name="todo_toggle"),
    path("bulk/", views.bulk_action, name="todo_bulk_action"),
    path("trash/", views.trash_view, name="trash"),
    path("trash/restore/<int:pk>/", views.restore_todo, name="todo_restore"),
    path("trash/delete/<int:pk>/", views.hard_delete_todo, name="todo_hard_delete"),
    path("categories/", views.category_list, name="category_list"),
    path("categories/delete/<int:pk>/", views.category_delete, name="category_delete"),
    path("stats/", views.stats_view, name="stats"),
    path("login/", auth_views.LoginView.as_view(template_name="todos/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("signup/", views.signup, name="signup"),
    path(
        "accounts/login/",
        auth_views.LoginView.as_view(template_name="todos/login.html"),
        name="accounts_login",
    ),
]
