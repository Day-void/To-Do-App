from django import forms

from .models import Category, Tag, Todo


class TodoForm(forms.ModelForm):
    tags = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-input",
                "placeholder": "comma, separated, tags",
            }
        ),
        help_text="Comma-separated. New tags are created automatically.",
    )

    class Meta:
        model = Todo
        fields = [
            "title",
            "description",
            "due_date",
            "priority",
            "category",
            "parent",
            "recurrence",
            "completed",
        ]
        widgets = {
            "title": forms.TextInput(
                attrs={"class": "form-input", "placeholder": "What needs to be done?"}
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-input",
                    "placeholder": "Add details (optional)",
                    "rows": 3,
                }
            ),
            "due_date": forms.DateInput(
                format="%Y-%m-%d", attrs={"class": "form-input", "type": "date"}
            ),
            "priority": forms.Select(attrs={"class": "form-input"}),
            "category": forms.Select(attrs={"class": "form-input"}),
            "parent": forms.Select(attrs={"class": "form-input"}),
            "recurrence": forms.Select(attrs={"class": "form-input"}),
            "completed": forms.CheckboxInput(attrs={"class": "checkbox"}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        if user is not None:
            self.fields["category"].queryset = Category.objects.filter(user=user)
            qs = Todo.objects.filter(user=user, is_deleted=False, parent__isnull=True)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            self.fields["parent"].queryset = qs
        self.fields["category"].required = False
        self.fields["parent"].required = False
        if self.instance.pk:
            self.initial["tags"] = ", ".join(
                self.instance.tags.values_list("name", flat=True)
            )

    def clean_tags(self):
        raw = self.cleaned_data.get("tags", "")
        return [name.strip() for name in raw.split(",") if name.strip()]

    def save(self, commit=True):
        instance = super().save(commit=commit)
        tag_names = self.cleaned_data.get("tags", [])

        def _sync_tags():
            tag_objs = []
            for name in tag_names:
                tag, _ = Tag.objects.get_or_create(user=self.user, name=name)
                tag_objs.append(tag)
            instance.tags.set(tag_objs)

        if commit:
            _sync_tags()
        else:
            original_save_m2m = self.save_m2m

            def save_m2m():
                original_save_m2m()
                _sync_tags()

            self.save_m2m = save_m2m
        return instance


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name"]
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "form-input", "placeholder": "e.g. Work, Home, School"}
            )
        }
