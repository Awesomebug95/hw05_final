import shutil
import tempfile
from http import HTTPStatus

from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Group, Post, User, Comment

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

USER = "User"
USER2 = 'User2'
HOME_URL = reverse('posts:index')
CREATE_POST_URL = reverse("posts:post_create")
PROFILE_URL = reverse("posts:profile",
                      kwargs={"username": USER})
LOGIN_URL = reverse("users:login")
REDIRECT_CREATE_URL = f'{LOGIN_URL}?next={CREATE_POST_URL}'

SMALL_GIF = (b'\x47\x49\x46\x38\x39\x61\x02\x00'
             b'\x01\x00\x80\x00\x00\x00\x00\x00'
             b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
             b'\x00\x00\x00\x2C\x00\x00\x00\x00'
             b'\x02\x00\x01\x00\x00\x02\x02\x0C'
             b'\x0A\x00\x3B')


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class FormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.USER_2 = "User_2"
        cls.TEXT = "Test text"
        cls.TEXT_2 = "Test text 2"
        cls.TEXT_3 = "Test text 3"
        cls.GROUP = "Test group"
        cls.GROUP_2 = "Test group 2"
        cls.GROUP_3 = "Test group 3"
        cls.DESC = "Test description"
        cls.DESC_2 = "Test description 2"
        cls.DESC_3 = "Test description 3"
        cls.SLUG = "test_group"
        cls.SLUG_2 = "test_group_2"
        cls.SLUG_3 = "test_group_3"
        cls.user = User.objects.create(username=USER)
        cls.user_2 = User.objects.create(username=cls.USER_2)

        cls.group_1 = Group.objects.create(
            title=cls.GROUP, description=cls.DESC, slug=cls.SLUG
        )
        cls.group_2 = Group.objects.create(
            title=cls.GROUP_2, description=cls.DESC_2, slug=cls.SLUG_2
        )
        cls.group_3 = Group.objects.create(
            title=cls.GROUP_3, description=cls.DESC_3, slug=cls.SLUG_3
        )
        cls.post = Post.objects.create(
            text=cls.TEXT,
            author=cls.user,
            group=cls.group_1
        )
        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.authorized_client2 = Client()
        cls.authorized_client2.force_login(cls.user_2)

        cls.EDIT_URL = reverse("posts:post_edit",
                               kwargs={"post_id": cls.post.id})
        cls.POST_URL = reverse("posts:post_detail",
                               kwargs={"post_id": cls.post.id})
        cls.COMMENT_URL = reverse("posts:add_comment",
                                  kwargs={"post_id": cls.post.pk})
        cls.COMMENT_REDIRECT_URL = f'{LOGIN_URL}?next={cls.COMMENT_URL}'
        cls.EDIT_REDIRECT_URL = f'{LOGIN_URL}?next={cls.EDIT_URL}'

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_post(self):
        """Тестируем создание поста."""
        Post.objects.all().delete()
        self.posts_count = Post.objects.count()
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        form_data = {
            "group": self.group_2.id,
            "text": self.TEXT,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            CREATE_POST_URL, data=form_data, follow=True
        )

        self.assertEqual(Post.objects.count(), self.posts_count + 1)
        self.assertRedirects(
            response,
            PROFILE_URL,
            HTTPStatus.FOUND,
        )
        post = response.context['page_obj'][0]
        self.assertEqual(post.text, form_data["text"])
        self.assertEqual(post.group.id, form_data["group"])
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.image.name,
                         f'{settings.POST_UPLOAD}/{uploaded.name}')

    def test_edit_post(self):
        """Тестируем изменение поста."""
        posts_count = Post.objects.count()
        uploaded = SimpleUploadedFile(
            name='small2.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        form_data = {
            "group": self.group_1.id,
            "text": self.TEXT_2,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            self.EDIT_URL,
            data=form_data,
            follow=True,
        )
        self.assertEqual(posts_count, Post.objects.count())
        self.assertRedirects(
            response,
            self.POST_URL,
            HTTPStatus.FOUND,
        )
        post = response.context['post']
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.author, self.post.author)
        self.assertEqual(post.group.id, form_data['group'])
        self.assertEqual(post.image.name,
                         f'{settings.POST_UPLOAD}/{uploaded.name}')

    def test_leave_comment_auth_user(self):
        """Тест авторизированный пользователь может оставить коммент."""
        form_data = {
            'text': self.TEXT,
        }
        self.authorized_client.post(
            self.COMMENT_URL,
            data=form_data,
            follow=True
        )
        self.assertEqual(self.post.comments.count(), 1)
        comment = self.post.comments.all()[0]
        self.assertEqual(comment.post.text, form_data['text'])
        self.assertEqual(comment.author, self.user)
        self.assertEqual(comment.post, self.post)

    def test_leave_comment_guest_user(self):
        """Тест гость не может оставить коммент."""
        comment_count = Comment.objects.count()
        response = self.guest_client.post(
            self.COMMENT_URL,
            data={'text': 'test_text'},
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comment_count)
        self.assertRedirects(response, self.COMMENT_REDIRECT_URL)

    def test_guest_create_post(self):
        """Тест Гость не может создать пост."""
        Post.objects.all().delete()
        posts_count = Post.objects.count()
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        form_data = {
            'text': self.TEXT,
            'group': self.group_2.id,
            'image': uploaded
        }
        response = self.guest_client.post(
            CREATE_POST_URL,
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertRedirects(response, REDIRECT_CREATE_URL)

    def test_guest_or_no_author_edit_post(self):
        """Тест гость не может редактировать пост."""
        uploaded = SimpleUploadedFile(
            name='small3.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        form_data = {
            'text': self.TEXT_2,
            'group': self.group_3.id,
            'image': uploaded
        }
        clients = [
            self.guest_client,
            self.authorized_client2
        ]
        for client in clients:
            with self.subTest(client=client):
                response = self.client.post(
                    self.EDIT_URL,
                    data=form_data,
                    follow=True
                )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(self.post.author, self.user)
        self.assertNotEqual(self.post.text, form_data['text'])
        self.assertNotEqual(self.post.group.id, form_data['group'])
        self.assertNotEqual(self.post.image, form_data['image'])
