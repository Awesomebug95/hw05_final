import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
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
USERNAME3 = 'author'

HOME_URL = reverse('posts:index')
CREATE_URL = reverse('posts:post_create')
FOLLOW_INDEX_URL = reverse('posts:follow_index')
GROUP_URL = reverse('posts:group_list', args=[SLUG])
GROUP_URL2 = reverse('posts:group_list', args=[SLUG2])
GROUP_URL3 = reverse('posts:group_list', args=[SLUG3])
PROFILE_URL = reverse('posts:profile', args=[USERNAME])
PROFILE_URL2 = reverse('posts:profile', args=[USERNAME2])
PROFILE_FOLLOW_URL = reverse('posts:profile_follow',
                             args=[USERNAME3])
PROFILE_UNFOLLOW_URL = reverse('posts:profile_unfollow',
                               args=[USERNAME2])

SMALL_GIF = (b'\x47\x49\x46\x38\x39\x61\x02\x00'
             b'\x01\x00\x80\x00\x00\x00\x00\x00'
             b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
             b'\x00\x00\x00\x2C\x00\x00\x00\x00'
             b'\x02\x00\x01\x00\x00\x02\x02\x0C'
             b'\x0A\x00\x3B')


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
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.author = User.objects.create_user(username=USERNAME3)
        cls.not_author = User.objects.create_user(username='not_author')
        cls.auth_client_not_author = Client()
        cls.auth_client_not_author.force_login(cls.not_author)
        cls.auth_client_author = Client()
        cls.auth_client_author.force_login(cls.author)
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user2,
            group=cls.group,
            text=TEXT,
            image=cls.uploaded,
        )
        Follow.objects.create(user=cls.user, author=cls.user2)
        cls.POST_URL = reverse('posts:post_detail', args=[cls.post.pk])

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_main_context(self):
        """Test Context."""
        paths = [
            HOME_URL,
            self.POST_URL,
            PROFILE_URL2,
            GROUP_URL,
            FOLLOW_INDEX_URL,
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
                self.assertEqual(post.image, self.post.image)

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
            FOLLOW_INDEX_URL
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
        response = self.authorized_client.get(HOME_URL).content
        Post.objects.create(
            text=TEXT, author=self.user
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertEqual(
            response, self.authorized_client.get(HOME_URL).content)
        cache.clear()
        self.assertNotEqual(
            response, self.authorized_client.get(HOME_URL).content)

    def test_follow_auth(self):
        follow_count = Follow.objects.count()
        self.auth_client_not_author.get(PROFILE_FOLLOW_URL)
        self.assertEqual(Follow.objects.count(), follow_count + 1)
        self.assertTrue(
            Follow.objects.filter(
                user=self.not_author, author=self.author).exists()
        )

    def test_unfollow_auth(self):
        follow_count = Follow.objects.count()
        self.authorized_client.get(PROFILE_UNFOLLOW_URL)
        self.assertEqual(Follow.objects.count(), follow_count - 1)
        self.assertFalse(
            Follow.objects.filter(user=self.user,
                                  author=self.user2).exists()

        )
