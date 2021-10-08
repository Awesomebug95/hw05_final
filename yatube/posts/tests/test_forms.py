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
CREATE_POST_URL = reverse("posts:post_create")
PROFILE_URL = reverse("posts:profile",
                      kwargs={"username": USER})
LOGIN_URL = reverse("users:login")


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class FormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.USER_2 = "User_2"
        cls.TEXT = "Test text"
        cls.TEXT_2 = "Test text 2"
        cls.GROUP = "Test group"
        cls.GROUP_2 = "Test group 2"
        cls.DESC = "Test description"
        cls.DESC_2 = "Test description 2"
        cls.SLUG = "test_group"
        cls.SLUG_2 = "test_group_2"
        cls.user = User.objects.create(username=USER)
        cls.user_2 = User.objects.create(username=cls.USER_2)

        cls.group_1 = Group.objects.create(
            title=cls.GROUP, description=cls.DESC, slug=cls.SLUG
        )
        cls.group_2 = Group.objects.create(
            title=cls.GROUP_2, description=cls.DESC_2, slug=cls.SLUG_2
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.small_gif = (b'\x47\x49\x46\x38\x39\x61\x02\x00'
                          b'\x01\x00\x80\x00\x00\x00\x00\x00'
                          b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
                          b'\x00\x00\x00\x2C\x00\x00\x00\x00'
                          b'\x02\x00\x01\x00\x00\x02\x02\x0C'
                          b'\x0A\x00\x3B')
        self.uploaded = SimpleUploadedFile(name='small_1.gif',
                                           content=self.small_gif,
                                           content_type='image/gif')
        self.post = Post.objects.create(
            text=self.TEXT,
            author=self.user,
            image=self.uploaded,
            group=self.group_1
        )
        self.EDIT_URL = reverse("posts:post_edit",
                                kwargs={"post_id": self.post.id})
        self.POST_URL = reverse("posts:post_detail",
                                kwargs={"post_id": self.post.id})
        self.COMMENT_URL = reverse("posts:add_comment",
                                   kwargs={"post_id": self.post.pk})

    def test_create_post(self):
        """Тестируем создание поста."""
        Post.objects.all().delete()
        self.posts_count = Post.objects.count()
        form_data = {"group": self.group_2.id, "text": self.TEXT}
        response = self.authorized_client.post(
            CREATE_POST_URL, data=form_data, follow=True
        )
        post = Post.objects.all()[0]
        self.assertEqual(Post.objects.count(), self.posts_count + 1)
        self.assertRedirects(
            response,
            PROFILE_URL,
            HTTPStatus.FOUND,
        )

        self.assertEqual(post.text, form_data["text"])
        self.assertEqual(post.group.id, form_data["group"])
        self.assertEqual(post.author, self.user)

    def test_edit_post(self):
        """Тестируем изменение поста."""
        posts_count = Post.objects.count()
        form_data = {
            "group": self.group_1.id,
            "text": self.TEXT_2,
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

    def test_create_post_with_picture(self):
        self.posts_count = Post.objects.count()
        response = self.authorized_client.get(reverse('posts:index'))
        first_obj = response.context['page_obj'][0]
        self.assertEqual(first_obj.group.title, self.group_1.title)
        self.assertEqual(first_obj.group.slug, self.group_1.slug)
        self.assertEqual(first_obj.group.description, self.group_1.description)
        self.assertTrue(first_obj.image, self.post.image)

    def test_leave_comment_auth_user(self):
        self.authorized_client.post(
            self.COMMENT_URL,
            data={'text': 'test_text'},
            follow=True
        )
        post = Comment.objects.first()
        self.assertEqual(post.text, 'test_text')

    def test_leave_comment_guest_user(self):
        response = self.guest_client.post(
            self.COMMENT_URL,
            data={'text': 'test_text'},
            follow=True
        )
        self.assertRedirects(
            response,
            LOGIN_URL + '?next=' + self.COMMENT_URL
        )
