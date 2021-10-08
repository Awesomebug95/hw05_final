from django.test import TestCase
from django.urls import reverse

USERNAME = 'USER'
SLUG = 'test_slug'
POST_ID = 1


class RoutesTest(TestCase):
    def test_routes(self):
        cases = [
            ['posts:index', [], '/'],
            ['posts:post_create', [], '/create/'],
            ['posts:post_edit', [POST_ID], f'/posts/{POST_ID}/edit/'],
            ['posts:group_list', [SLUG], f'/group/{SLUG}/'],
            ['posts:profile', [USERNAME], f'/profile/{USERNAME}/'],
            ['posts:post_detail', [POST_ID], f'/posts/{POST_ID}/'],
        ]
        for route, args, adress in cases:
            with self.subTest(route=route):
                self.assertEqual(reverse(route, args=args), adress)
