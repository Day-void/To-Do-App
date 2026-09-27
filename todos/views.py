from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from .forms import CategoryForm, TodoForm
from .models import Category, Todo

SMART_VIEWS = {"all", "today", "upcoming", "overdue"}


class TodoListView(LoginRequiredMixin, ListView):
    model = Todo
    template_name = "todos/todo_list.html"
    context_object_name = "todos"
    paginate_by = 15

    def get_queryset(self):
        today = timezone.localdate()
        queryset = Todo.objects.filter(
            user=self.request.user, is_deleted=False, parent__isnull=True
        )

        view = self.request.GET.get("view", "all")
        if view == "today":
            queryset = queryset.filter(due_date=today)
        elif view == "upcoming":
            queryset = queryset.filter(due_date__gt=today)
        elif view == "overdue":
            queryset = queryset.filter(due_date__lt=today, completed=False)

        if not self.request.GET.get("show_completed"):
            queryset = queryset.filter(completed=False)

        search_query = self.request.GET.get("search")
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query)
                | Q(description__icontains=search_query)
                | Q(category__name__icontains=search_query)
                | Q(tags__name__icontains=search_query)
            ).distinct()

        category_id = self.request.GET.get("category")
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        priority = self.request.GET.get("priority")
        if priority:
            queryset = queryset.filter(priority=priority)

        return queryset.prefetch_related("tags", "subtasks").select_related("category")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.localdate()
        base = Todo.objects.filter(
            user=self.request.user, is_deleted=False, parent__isnull=True
        )
        context["categories"] = Category.objects.filter(user=self.request.user)
        context["priority_choices"] = Todo.PRIORITY_CHOICES
        context["current_view"] = self.request.GET.get("view", "all")
        context["show_completed"] = bool(self.request.GET.get("show_completed"))
        context["counts"] = {
            "all": base.filter(completed=False).count(),
            "today": base.filter(due_date=today, completed=False).count(),
            "upcoming": base.filter(due_date__gt=today, completed=False).count(),
            "overdue": base.filter(due_date__lt=today, completed=False).count(),
        }
        return context


class TodoCreateView(LoginRequiredMixin, CreateView):
    model = Todo
    form_class = TodoForm
    template_name = "todos/todo_form.html"
    success_url = reverse_lazy("todo_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class TodoUpdateView(LoginRequiredMixin, UpdateView):
    model = Todo
    form_class = TodoForm
    template_name = "todos/todo_form.html"
    success_url = reverse_lazy("todo_list")

    def get_queryset(self):
        return Todo.objects.filter(user=self.request.user, is_deleted=False)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class TodoDeleteView(LoginRequiredMixin, DeleteView):
    """Soft-deletes: the task moves to Trash instead of vanishing forever."""

    model = Todo
    template_name = "todos/todo_confirm_delete.html"
    success_url = reverse_lazy("todo_list")

    def get_queryset(self):
        return Todo.objects.filter(user=self.request.user, is_deleted=False)

    def form_valid(self, form):
        self.object = self.get_object()
        self.object.soft_delete()
        messages.success(self.request, "Task moved to Trash.")
        return redirect(self.success_url)


@login_required
def toggle_todo(request, pk):
    item = get_object_or_404(Todo, pk=pk, user=request.user, is_deleted=False)
    item.completed = not item.completed
    item.completed_at = timezone.now() if item.completed else None
    item.save(update_fields=["completed", "completed_at"])
    if item.completed:
        spawned = item.spawn_next_occurrence()
        if spawned:
            messages.info(request, f'Next occurrence of "{item.title}" was scheduled.')
    return redirect(request.META.get("HTTP_REFERER") or "todo_list")


@login_required
def bulk_action(request):
    if request.method != "POST":
        return redirect("todo_list")

    ids = request.POST.getlist("selected")
    action = request.POST.get("action")
    qs = Todo.objects.filter(user=request.user, id__in=ids, is_deleted=False)

    if action == "complete":
        qs.update(completed=True, completed_at=timezone.now())
        messages.success(request, f"Marked {qs.count()} task(s) complete.")
    elif action == "delete":
        count = qs.count()
        for item in qs:
            item.soft_delete()
        messages.success(request, f"Moved {count} task(s) to Trash.")

    return redirect("todo_list")


@login_required
def trash_view(request):
    items = Todo.objects.filter(user=request.user, is_deleted=True).order_by("-deleted_at")
    return render(request, "todos/trash.html", {"todos": items})


@login_required
def restore_todo(request, pk):
    item = get_object_or_404(Todo, pk=pk, user=request.user, is_deleted=True)
    item.restore()
    messages.success(request, f'"{item.title}" restored.')
    return redirect("trash")


@login_required
def hard_delete_todo(request, pk):
    item = get_object_or_404(Todo, pk=pk, user=request.user, is_deleted=True)
    item.delete()
    messages.success(request, "Task permanently deleted.")
    return redirect("trash")


@login_required
def category_list(request):
    if request.method == "POST":
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.user = request.user
            category.save()
            messages.success(request, f'Category "{category.name}" created.')
            return redirect("category_list")
    else:
        form = CategoryForm()
    categories = Category.objects.filter(user=request.user).annotate(
        todo_count=Count("todos")
    )
    return render(
        request, "todos/category_list.html", {"form": form, "categories": categories}
    )


@login_required
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk, user=request.user)
    category.delete()
    messages.success(request, "Category deleted.")
    return redirect("category_list")


@login_required
def stats_view(request):
    todos = Todo.objects.filter(user=request.user, is_deleted=False, parent__isnull=True)
    total = todos.count()
    completed = todos.filter(completed=True).count()
    overdue = sum(1 for t in todos if t.is_overdue)
    by_priority = {
        label: todos.filter(priority=value, completed=False).count()
        for value, label in Todo.PRIORITY_CHOICES
    }
    context = {
        "total": total,
        "completed": completed,
        "pending": total - completed,
        "overdue": overdue,
        "completion_rate": round((completed / total) * 100) if total else 0,
        "by_priority": by_priority,
    }
    return render(request, "todos/stats.html", context)


def signup(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("todo_list")
    else:
        form = UserCreationForm()
    return render(request, "todos/signup.html", {"form": form})
