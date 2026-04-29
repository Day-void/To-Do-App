from django.urls import path
from .import views
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('', views.todoListView.as_view(), name='todo_list'),
    path('create/', views.todoCreateView.as_view(), name='todo_create'),
    path('edit/<int:pk>/', views.todoUpdateView.as_view(), name='todo_edit'),
    path('delete/<int:pk>/', views.tododeleteView.as_view(), name='todo_delete'),
    path('toggle/<int:pk>/', views.toggle_todo, name='todo_toggle'),
    path('login/', auth_views.LoginView.as_view(template_name='todos/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('signup/', views.signup, name='signup'),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='todos/login.html'), name='accounts_login'),

]
