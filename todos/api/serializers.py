from rest_framework import serializers

from ..models import Category, Tag, Todo


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name"]


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name"]


class TodoSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    tag_names = serializers.ListField(
        child=serializers.CharField(max_length=50), write_only=True, required=False
    )
    is_overdue = serializers.BooleanField(read_only=True)

    class Meta:
        model = Todo
        fields = [
            "id", "title", "description", "completed", "completed_at",
            "due_date", "created_at", "updated_at", "priority", "category",
            "tags", "tag_names", "parent", "recurrence", "is_overdue",
        ]
        read_only_fields = ["created_at", "updated_at", "completed_at"]

    def validate_category(self, value):
        request = self.context["request"]
        if value and value.user_id != request.user.id:
            raise serializers.ValidationError("Not your category.")
        return value

    def _sync_tags(self, todo, names):
        tags = []
        for name in names:
            name = name.strip()
            if not name:
                continue
            tag, _ = Tag.objects.get_or_create(user=self.context["request"].user, name=name)
            tags.append(tag)
        todo.tags.set(tags)

    def create(self, validated_data):
        names = validated_data.pop("tag_names", [])
        validated_data["user"] = self.context["request"].user
        todo = super().create(validated_data)
        self._sync_tags(todo, names)
        return todo

    def update(self, instance, validated_data):
        names = validated_data.pop("tag_names", None)
        todo = super().update(instance, validated_data)
        if names is not None:
            self._sync_tags(todo, names)
        return todo
