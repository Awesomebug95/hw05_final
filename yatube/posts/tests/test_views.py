import shutil
import tempfile

from django.conf import settings
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.core.cache import cache

from posts.models import Group, Post, User, Follow

from yatube.settings import PAGINATOR_CONST

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

SLUG = 'test-slug'
SLUG2 = 'test-slug-2'
SLUG3 = 'test-slug-3'
TEXT = 'Тестовый текст'
TEXT2 = 'Тестовый текст2'
TEXT3 = 'Тестовый текст3'
TITLE = 'Тестовый заголовок'
TITLE2 = 'Тестовый заголовок2'
TITLE3 = 'Тестовый заголовок3'
USERNAME = 'User'
USERNAME2 = 'User2'

HOME_URL = reverse('posts:index')
CREATE_URL = reverse('posts:post_create')
GROUP_URL = reverse('posts:group_list', args=[SLUG])
GROUP_URL2 = reverse('posts:group_list', args=[SLUG2])
GROUP_URL3 = reverse('posts:group_list', args=[SLUG3])
PROFILE_URL = reverse('posts:profile', args=[USERNAME])
PROFILE_URL2 = reverse('posts:profile', args=[USERNAME2])


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title=TITLE,
            description=TEXT,
            slug=SLUG
        )
        cls.group2 = Group.objects.create(
            title=TITLE2,
            description=TEXT2,
            slug=SLUG2
        )
        cls.group3 = Group.objects.create(
            title=TITLE3,
            description=TEXT3,
            slug=SLUG3
        )
        cls.user = User.objects.create_user(username=USERNAME)
        cls.user2 = User.objects.create_user(username=USERNAME2)
        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            text=TEXT
        )
        cls.POST_URL = reverse('posts:post_detail', args=[cls.post.pk])
        cls.EDIT_URL = reverse('posts:post_edit', args=[cls.post.pk])

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author = User.objects.create_user(username='author')
        self.not_author = User.objects.create_user(username='not_author')
        self.auth_client_not_author = Client()
        self.auth_client_not_author.force_login(self.not_author)
        self.auth_client_author = Client()
        self.auth_client_author.force_login(self.author)
        self.PROFILE_FOLLOW_URL = reverse('posts:profile_follow',
                                          args=[self.author.username])
        self.PROFILE_UNFOLLOW_URL = reverse('posts:profile_unfollow',
                                            args=[self.author.username])

    def test_main_context(self):
        """Test Context."""
        paths = [
            HOME_URL,
            self.POST_URL,
            PROFILE_URL,
            GROUP_URL
        ]
        for address in paths:
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                if address == self.POST_URL:
                    post = response.context['post']
                else:
                    self.assertEqual(len(response.context['page_obj']), 1)
                    post = response.context['page_obj'][0]
                self.assertEqual(post.author, self.post.author)
                self.assertEqual(post.group, self.post.group)
                self.assertEqual(post.text, self.post.text)

    def test_paginator_on_pages(self):
        """Тест работы пагинатора на страницах."""
        for post in range(PAGINATOR_CONST):
            Post.objects.create(
                author=self.user2,
                group=self.group3,
                text='text'
            )
        paginator_urls = [
            HOME_URL,
            GROUP_URL3,
            PROFILE_URL2,
        ]
        for page in paginator_urls:
            with self.subTest(page=page):
                response = self.authorized_client.get(page)
                self.assertEqual(
                    len(response.context['page_obj']),
                    PAGINATOR_CONST
                )

    def test_post_not_in_group(self):
        response = self.authorized_client.get(GROUP_URL2)
        self.assertNotIn(self.post, response.context['page_obj'])

    def test_fixtures_profile(self):
        response = self.authorized_client.get(PROFILE_URL)
        self.assertEqual(response.context['author'], self.user)

    def test_fixtures_group(self):
        response = self.authorized_client.get(GROUP_URL)
        group = response.context['group']
        self.assertEqual(group.slug, self.group.slug)
        self.assertEqual(group.title, self.group.title)
        self.assertEqual(group.description, self.group.description)

    def test_cache(self):
        posts_count = Post.objects.count()
        response = self.authorized_client.get(reverse('posts:index')).content
        Post.objects.create(
            text=TEXT, author=self.user, group=self.group2
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertEqual(
            response, self.authorized_client.get(HOME_URL).content)
        cache.clear()
        self.assertNotEqual(
            response, self.authorized_client.get(HOME_URL).content)

    def test_follow_unfollow_auth(self):
        follow_count = Follow.objects.count()
        self.auth_client_not_author.get(self.PROFILE_FOLLOW_URL)
        self.assertEqual(Follow.objects.count(), follow_count + 1)
        self.assertTrue(
            Follow.objects.filter(
                user=self.not_author, author=self.author).exists()
        )
        self.auth_client_not_author.get(self.PROFILE_UNFOLLOW_URL)
        self.assertEqual(Follow.objects.count(), follow_count)
        self.assertFalse(
            Follow.objects.filter(user=self.not_author,
                                  author=self.author).exists()
        )

    def test_new_post_follow(self):
        following = User.objects.create(username='following')
        Follow.objects.create(user=self.user, author=following)
        post = Post.objects.create(author=following, text=TEXT)
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertIn(post, response.context['page_obj'])
        response = self.auth_client_author.get(reverse('posts:follow_index'))
        self.assertNotIn(post, response.context['page_obj'])
