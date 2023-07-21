from django.test import Client, TestCase
from django.urls import reverse
from kobo.django.auth.models import User


class LoginRequiredMiddlewareTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.url = reverse('user/list')
        self._prepare_user()

    def _prepare_user(self):
        User.objects.create_user(
            username='test',
            email='user@example.com',
            password='test')
        # Create staff user
        User.objects.create_user(
            username='test_staff',
            email='user_staff@example.com',
            password='test',
            is_staff=True)

    def test_anonymous_access_user_list(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_authenticated_access_user_list(self):
        self.client.login(username='test', password='test')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_staff_access_user_list(self):
        self.client.login(username='test_staff', password='test')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_non_user_list_view(self):
        # views other than the user/list under info should be working fine.
        # FIXME: change of upstream kobo may break this test
        url = reverse('worker/list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
