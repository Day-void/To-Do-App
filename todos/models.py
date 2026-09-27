from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


class Category(models.Model):
    """A category/list, scoped to the user who created it.

    Categories used to be global (visible to every user). Scoping them to
    a user closes that data leak and also lets each user build their own
    taxonomy without colliding with anyone else's.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="categories",
    )
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "name"], name="unique_category_per_user"
            )
        ]

    def __str__(self):
        return self.name


class Tag(models.Model):
    """Free-form labels, many-to-many with tasks (unlike Category, a task
    can have more than one tag)."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tags",
    )
    name = models.CharField(max_length=50)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["user", "name"], name="unique_tag_per_user")
        ]

    def __str__(self):
        return self.name


class Todo(models.Model):
    PRIORITY_LOW = 1
    PRIORITY_MEDIUM = 2
    PRIORITY_HIGH = 3
    PRIORITY_CHOICES = [
        (PRIORITY_LOW, "Low"),
        (PRIORITY_MEDIUM, "Medium"),
        (PRIORITY_HIGH, "High"),
    ]

    RECURRENCE_NONE = "none"
    RECURRENCE_DAILY = "daily"
    RECURRENCE_WEEKLY = "weekly"
    RECURRENCE_MONTHLY = "monthly"
    RECURRENCE_CHOICES = [
        (RECURRENCE_NONE, "Does not repeat"),
        (RECURRENCE_DAILY, "Daily"),
        (RECURRENCE_WEEKLY, "Weekly"),
        (RECURRENCE_MONTHLY, "Monthly"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="todos",
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    priority = models.PositiveSmallIntegerField(
        choices=PRIORITY_CHOICES, default=PRIORITY_MEDIUM
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="todos",
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name="todos")

    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="subtasks",
        help_text="Set this to make the task a subtask of another task.",
    )

    recurrence = models.CharField(
        max_length=10, choices=RECURRENCE_CHOICES, default=RECURRENCE_NONE
    )

    # Soft delete: hard-deleting a task with one misclick is unrecoverable.
    # is_deleted tasks are hidden from every normal view but kept for 30
    # days (see management command / admin action) before real deletion.
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["completed", "due_date", "-priority", "created_at"]

    def __str__(self):
        return self.title

    @property
    def is_overdue(self):
        return bool(
            self.due_date
            and not self.completed
            and self.due_date < timezone.localdate()
        )

    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=["is_deleted", "deleted_at"])

    def restore(self):
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=["is_deleted", "deleted_at"])

    def _next_due_date(self):
        if not self.due_date:
            return None
        if self.recurrence == self.RECURRENCE_DAILY:
            return self.due_date + timedelta(days=1)
        if self.recurrence == self.RECURRENCE_WEEKLY:
            return self.due_date + timedelta(weeks=1)
        if self.recurrence == self.RECURRENCE_MONTHLY:
            month = self.due_date.month % 12 + 1
            year = self.due_date.year + (self.due_date.month // 12)
            day = min(
                self.due_date.day,
                [31, 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28,
                 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1],
            )
            return self.due_date.replace(year=year, month=month, day=day)
        return None

    def spawn_next_occurrence(self):
        """If this task repeats, create the next instance of it."""
        if self.recurrence == self.RECURRENCE_NONE:
            return None
        next_due = self._next_due_date()
        clone = Todo.objects.create(
            user=self.user,
            title=self.title,
            description=self.description,
            due_date=next_due,
            priority=self.priority,
            category=self.category,
            recurrence=self.recurrence,
        )
        clone.tags.set(self.tags.all())
        return clone
