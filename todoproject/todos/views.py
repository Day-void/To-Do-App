from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q 
from .models import todo
from .forms import TodoForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.shortcuts import redirect

class todoListView(LoginRequiredMixin, ListView):
    model = todo
    template_name = 'todos/todo_list.html'
    context_object_name = 'todos'

    def get_queryset(self):
        queryset = todo.objects.filter(user=self.request.user)
        
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) | 
                Q(description__icontains=search_query)
            )
        return queryset

class todoCreateView(LoginRequiredMixin, CreateView):
    model = todo
    form_class = TodoForm
    template_name = 'todos/todo_form.html'
    success_url = reverse_lazy('todo_list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

class todoUpdateView(LoginRequiredMixin, UpdateView):
    model = todo
    form_class = TodoForm
    template_name = 'todos/todo_form.html'
    success_url = reverse_lazy('todo_list')

    def get_queryset(self):
    
        return todo.objects.filter(user=self.request.user)

class tododeleteView(LoginRequiredMixin, DeleteView):
    model = todo
    template_name = 'todos/todo_confirm_delete.html'
    success_url = reverse_lazy('todo_list')

    def get_queryset(self):
        return todo.objects.filter(user=self.request.user)

def toggle_todo(request, pk):
    item = get_object_or_404(todo, pk=pk, user=request.user)
    item.completed = not item.completed
    item.save()
    return redirect('todo_list')


def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('todo_list')
    else:
        form = UserCreationForm()
    return render(request, 'todos/signup.html', {'form': form})


