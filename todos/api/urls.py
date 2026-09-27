from rest_framework.routers import DefaultRouter

from .views import CategoryViewSet, TagViewSet, TodoViewSet

router = DefaultRouter()
router.register("todos", TodoViewSet, basename="api-todo")
router.register("categories", CategoryViewSet, basename="api-category")
router.register("tags", TagViewSet, basename="api-tag")

urlpatterns = router.urls
