import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Category, Todo

User = get_user_model()


class TodoOwnershipTests(TestCase):
    """The bug this project used to have: users could see/edit/delete
    each other's data. These tests pin that down."""

    def setUp(self):
        self.alice = User.objects.create_user("alice", password="pass12345")
        self.bob = User.objects.create_user("bob", password="pass12345")
        self.alice_todo = Todo.objects.create(user=self.alice, title="Alice's task")
        self.bob_todo = Todo.objects.create(user=self.bob, title="Bob's task")

    def test_list_view_only_shows_own_todos(self):
        self.client.login(username="alice", password="pass12345")
        response = self.client.get(reverse("todo_list"))
        titles = [t.title for t in response.context["todos"]]
        self.assertIn("Alice's task", titles)
        self.assertNotIn("Bob's task", titles)

    def test_cannot_edit_someone_elses_todo(self):
        self.client.login(username="alice", password="pass12345")
        response = self.client.get(reverse("todo_edit", args=[self.bob_todo.pk]))
        self.assertEqual(response.status_code, 404)

    def test_cannot_delete_someone_elses_todo(self):
        self.client.login(username="alice", password="pass12345")
        response = self.client.post(reverse("todo_delete", args=[self.bob_todo.pk]))
        self.assertEqual(response.status_code, 404)
        self.bob_todo.refresh_from_db()
        self.assertFalse(self.bob_todo.is_deleted)

    def test_cannot_toggle_someone_elses_todo(self):
        self.client.login(username="alice", password="pass12345")
        self.client.post(reverse("todo_toggle", args=[self.bob_todo.pk]))
        self.bob_todo.refresh_from_db()
        self.assertFalse(self.bob_todo.completed)

    def test_anonymous_user_redirected_to_login(self):
        response = self.client.get(reverse("todo_list"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_toggle_requires_login(self):
        response = self.client.post(reverse("todo_toggle", args=[self.alice_todo.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)


class CategoryScopingTests(TestCase):
    """Categories used to be global; confirm they're now per-user."""

    def setUp(self):
        self.alice = User.objects.create_user("alice", password="pass12345")
        self.bob = User.objects.create_user("bob", password="pass12345")
        self.alice_cat = Category.objects.create(user=self.alice, name="Work")

    def test_category_filter_dropdown_only_shows_own_categories(self):
        self.client.login(username="bob", password="pass12345")
        response = self.client.get(reverse("todo_list"))
        self.assertNotIn(self.alice_cat, response.context["categories"])

    def test_category_filtering_works(self):
        cat = Category.objects.create(user=self.alice, name="Home")
        t1 = Todo.objects.create(user=self.alice, title="Fix sink", category=cat)
        Todo.objects.create(user=self.alice, title="Write report", category=self.alice_cat)
        self.client.login(username="alice", password="pass12345")
        response = self.client.get(reverse("todo_list"), {"category": cat.pk})
        titles = [t.title for t in response.context["todos"]]
        self.assertEqual(titles, ["Fix sink"])


class SoftDeleteTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("alice", password="pass12345")
        self.todo = Todo.objects.create(user=self.user, title="Task")
        self.client.login(username="alice", password="pass12345")

    def test_delete_soft_deletes(self):
        self.client.post(reverse("todo_delete", args=[self.todo.pk]))
        self.todo.refresh_from_db()
        self.assertTrue(self.todo.is_deleted)
        self.assertTrue(Todo.objects.filter(pk=self.todo.pk).exists())

    def test_deleted_todo_hidden_from_list(self):
        self.todo.soft_delete()
        response = self.client.get(reverse("todo_list"))
        self.assertNotIn(self.todo, response.context["todos"])

    def test_restore_brings_it_back(self):
        self.todo.soft_delete()
        self.client.post(reverse("todo_restore", args=[self.todo.pk]))
        self.todo.refresh_from_db()
        self.assertFalse(self.todo.is_deleted)


class RecurrenceTests(TestCase):
    def test_completing_a_daily_task_spawns_the_next_one(self):
        user = User.objects.create_user("alice", password="pass12345")
        todo = Todo.objects.create(
            user=user,
            title="Water plants",
            due_date=datetime.date(2026, 1, 1),
            recurrence=Todo.RECURRENCE_DAILY,
        )
        self.client.login(username="alice", password="pass12345")
        self.client.post(reverse("todo_toggle", args=[todo.pk]))
        todo.refresh_from_db()
        self.assertTrue(todo.completed)
        next_todo = Todo.objects.exclude(pk=todo.pk).get(user=user)
        self.assertEqual(next_todo.due_date, datetime.date(2026, 1, 2))
        self.assertFalse(next_todo.completed)


class OverdueTests(TestCase):
    def test_is_overdue_true_for_past_incomplete(self):
        user = User.objects.create_user("alice", password="pass12345")
        todo = Todo.objects.create(
            user=user, title="Old task", due_date=datetime.date(2000, 1, 1)
        )
        self.assertTrue(todo.is_overdue)

    def test_is_overdue_false_once_completed(self):
        user = User.objects.create_user("alice", password="pass12345")
        todo = Todo.objects.create(
            user=user,
            title="Old task",
            due_date=datetime.date(2000, 1, 1),
            completed=True,
        )
        self.assertFalse(todo.is_overdue)


class SignupTests(TestCase):
    def test_signup_logs_user_in_and_redirects_to_list(self):
        response = self.client.post(
            reverse("signup"),
            {
                "username": "newuser",
                "password1": "a-strong-password123",
                "password2": "a-strong-password123",
            },
        )
        self.assertRedirects(response, reverse("todo_list"))
        self.assertTrue(User.objects.filter(username="newuser").exists())
