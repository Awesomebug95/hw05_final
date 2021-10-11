from django.test import TestCase
from django.urls import reverse

USERNAME = 'USER'
SLUG = 'test_slug'
POST_ID = 1


class RoutesTest(TestCase):
    def test_routes(self):
        cases = [
            ['index', [],
             '/'],
            ['post_create', [],
             '/create/'],
            ['post_edit', [POST_ID],
             f'/posts/{POST_ID}/edit/'],
            ['group_list', [SLUG],
             f'/group/{SLUG}/'],
            ['profile', [USERNAME],
             f'/profile/{USERNAME}/'],
            ['post_detail', [POST_ID],
             f'/posts/{POST_ID}/'],
            ['follow_index', [],
             '/follow/'],
            ['profile_follow', [USERNAME],
             f'/profile/{USERNAME}/follow/'],
            ['profile_unfollow', [USERNAME],
             f'/profile/{USERNAME}/unfollow/'],
            ['add_comment', [POST_ID],
             f'/posts/{POST_ID}/comment'],
        ]
        for route, args, adress in cases:
            with self.subTest(route=route):
                self.assertEqual(reverse('posts:' + route, args=args), adress)
