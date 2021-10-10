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

HOME_URL = reverse('posts:index')
CREATE_URL = reverse('posts:post_create')
GROUP_URL = reverse('posts:group_list', args=[SLUG])
PROFILE_URL = reverse('posts:profile', args=[USER])
BROKEN_PAGE_URL = 'gimmieaburger/please/'
REDIRECT_CREATE_URL = (reverse('users:login') + '?next=' + CREATE_URL)
LOGIN_URL = reverse('users:login')
FOLLOW_INDEX_URL = reverse('posts:follow_index')
REDIRECT_FOLLOW_INDEX_URL = (LOGIN_URL + '?next=' + FOLLOW_INDEX_URL)
FOLLOW_PROFILE_URL = reverse('posts:profile_follow', args=[USER])
REDIRECT_FOLLOW_PROFILE_URL = (reverse('users:login') + '?next='
                               + FOLLOW_PROFILE_URL)
UNFOLLOW_PROFILE_URL = reverse('posts:profile_unfollow', args=[USER])
REDIRECT_UNFOLLOW_PROFILE_URL = (reverse('users:login') + '?next='
                                 + UNFOLLOW_PROFILE_URL)


class URLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username=USER)
        cls.user_2 = User.objects.create(username=USER_2)
        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user_2)
        cls.authorized_client_2 = Client()
        cls.authorized_client_2.force_login(cls.user)
        Group.objects.create(
            title=GROUP, description=DESC, slug=SLUG
        )
        cls.post = Post.objects.create(
            text=TEXT, author=cls.user
        )
        cls.POST_URL = reverse('posts:post_detail', args=[cls.post.pk])
        cls.EDIT_URL = reverse('posts:post_edit', args=[cls.post.pk])
        cls.COMMENT_URL = reverse('posts:add_comment', args=[cls.post.pk])
        cls.REDIRECT_EDIT_URL = (LOGIN_URL + '?next=' + cls.EDIT_URL)
        cls.REDIRECT_COMMENT_URL = (LOGIN_URL + '?next=' + cls.COMMENT_URL)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        pass

    def test_url_pages(self):
        """Тестируем ответы страниц."""
        cases = [
            [HOME_URL, self.guest_client, 200],
            [GROUP_URL, self.guest_client, 200],
            [PROFILE_URL, self.guest_client, 200],
            [self.POST_URL, self.guest_client, 200],
            [self.EDIT_URL, self.authorized_client_2, 200],
            [CREATE_URL, self.authorized_client, 200],
            [BROKEN_PAGE_URL, self.guest_client, 404],
            [CREATE_URL, self.guest_client, 302],
            [self.EDIT_URL, self.authorized_client, 302],
            [self.EDIT_URL, self.guest_client, 302],
            [FOLLOW_INDEX_URL, self.authorized_client, 200],
            [FOLLOW_INDEX_URL, self.guest_client, 302],
            [FOLLOW_PROFILE_URL, self.authorized_client, 302],
            [FOLLOW_PROFILE_URL, self.guest_client, 302],
            [UNFOLLOW_PROFILE_URL, self.authorized_client, 302],
            [UNFOLLOW_PROFILE_URL, self.guest_client, 302],
            [self.COMMENT_URL, self.authorized_client, 302],
            [self.COMMENT_URL, self.guest_client, 302],
        ]
        for url, client, code in cases:
            with self.subTest(url=url, client=client, code=code):
                self.assertEqual(client.get(url).status_code, code)

    def test_redirect_pages(self):
        """Тестируем редирект."""
        cases = [
            [CREATE_URL, True, self.guest_client, REDIRECT_CREATE_URL],
            [self.EDIT_URL, True, self.authorized_client, HOME_URL],
            [self.EDIT_URL, True, self.guest_client, self.REDIRECT_EDIT_URL],
            [FOLLOW_INDEX_URL, True, self.guest_client,
             REDIRECT_FOLLOW_INDEX_URL],
            [FOLLOW_PROFILE_URL, True, self.authorized_client, PROFILE_URL],
            [FOLLOW_PROFILE_URL, True, self.guest_client,
             REDIRECT_FOLLOW_PROFILE_URL],
            [UNFOLLOW_PROFILE_URL, True, self.authorized_client, PROFILE_URL],
            [UNFOLLOW_PROFILE_URL, True, self.guest_client,
             REDIRECT_UNFOLLOW_PROFILE_URL],
            [self.COMMENT_URL, True, self.authorized_client, self.POST_URL],
            [self.COMMENT_URL, True, self.guest_client,
             self.REDIRECT_COMMENT_URL],
        ]
        for url, follow, client, redirect in cases:
            with self.subTest(url=url, client=client, redirect=redirect):
                self.assertRedirects(client.get(url, follow=follow), redirect)

    def test_template_pages(self):
        """Тестируем шаблоны"""
        cases = [
            [HOME_URL, self.guest_client, 'posts/index.html'],
            [GROUP_URL, self.guest_client, 'posts/group_list.html'],
            [PROFILE_URL, self.guest_client, 'posts/profile.html'],
            [self.POST_URL, self.guest_client, 'posts/post_detail.html'],
            [self.EDIT_URL, self.authorized_client_2,
             'posts/create_post.html'],
            [CREATE_URL, self.authorized_client, 'posts/create_post.html'],
            [BROKEN_PAGE_URL, self.guest_client, 'core/404.html'],
            [FOLLOW_INDEX_URL, self.authorized_client, 'posts/follow.html']
        ]
        for url, client, template in cases:
            with self.subTest(url=url, client=client):
                self.assertTemplateUsed(client.get(url), template)
