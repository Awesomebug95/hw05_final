from django.test import TestCase

from ..models import Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="auth")
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="Тестовый слаг",
            description="Тестовое описание",
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text="Тестовая группа с очень длинным текстом",
        )
        cls.model_str = {
            cls.group: cls.group.title,
            cls.post: cls.post.text[:15],
        }

    def test_str_method_models(self):
        """Проверяем, что у моделей корректно работает __str__."""
        for model, value in self.model_str.items():
            with self.subTest(model=model):
                act = str(model)
                self.assertEqual(act, value)
