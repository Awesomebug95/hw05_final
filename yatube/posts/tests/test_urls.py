import shutil
import tempfile

from django.conf import settings
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
USER = "User"
USER_2 = "User_2"
TEXT = "Test text"
TEXT_2 = "Test text_2"
GROUP = "Test group"
GROUP_2 = "Test group 2"
DESC = "Test description"
DESC_2 = "Test description 2"
SLUG = "test_group"
SLUG_2 = "test_group_2"

HOME = reverse('posts:index')
CREATE = reverse('posts:post_create')
GROUP = reverse('posts:group_list', args=[SLUG])
PROFILE = reverse('posts:profile', args=[USER])
BROKEN_PAGE_URL = 'gimmieaburger/please/'
REDIRECT_CREATE_URL = (reverse('users:login') + '?next=' + CREATE)
LOGIN_URL = reverse('users:login')


class URLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username=USER)
        cls.user_2 = User.objects.create(username=USER_2)
        Group.objects.create(
            title=GROUP, description=DESC, slug=SLUG
        )
        cls.post = Post.objects.create(
            text=TEXT, author=cls.user
        )
        cls.POST_URL = reverse('posts:post_detail', args=[cls.post.pk])
        cls.EDIT_URL = reverse('posts:post_edit', args=[cls.post.pk])
        cls.REDIRECT_EDIT_URL = (LOGIN_URL + '?next=' + cls.EDIT_URL)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user_2)
        self.authorized_client_2 = Client()
        self.authorized_client_2.force_login(self.user)

    def test_url_pages(self):
        """Тестируем ответы страниц."""
        cases = [
            [HOME, self.guest_client, 200],
            [GROUP, self.guest_client, 200],
            [PROFILE, self.guest_client, 200],
            [self.POST_URL, self.guest_client, 200],
            [self.EDIT_URL, self.authorized_client_2, 200],
            [CREATE, self.authorized_client, 200],
            [BROKEN_PAGE_URL, self.guest_client, 404],
            [CREATE, self.guest_client, 302],
            [self.EDIT_URL, self.authorized_client, 302],
            [self.EDIT_URL, self.guest_client, 302]
        ]
        for url, client, code in cases:
            with self.subTest(url=url):
                self.assertEqual(client.get(url).status_code, code)

    def test_redirect_pages(self):
        """Тестируем редирект."""
        cases = [
            [CREATE, True, self.guest_client, REDIRECT_CREATE_URL],
            [self.EDIT_URL, True, self.authorized_client, HOME],
            [self.EDIT_URL, True, self.guest_client, self.REDIRECT_EDIT_URL]
        ]
        for url, follow, client, redirect in cases:
            with self.subTest(url=url):
                self.assertRedirects(client.get(url, follow=follow), redirect)

    def test_template_pages(self):
        """Тестируем шаблоны"""
        cases = [
            [HOME, self.guest_client, 'posts/index.html'],
            [GROUP, self.guest_client, 'posts/group_list.html'],
            [PROFILE, self.guest_client, 'posts/profile.html'],
            [self.POST_URL, self.guest_client, 'posts/post_detail.html'],
            [self.EDIT_URL, self.authorized_client_2,
             'posts/create_post.html'],
            [CREATE, self.authorized_client, 'posts/create_post.html'],
        ]
        for url, client, template in cases:
            with self.subTest(url=url):
                self.assertTemplateUsed(client.get(url), template)
