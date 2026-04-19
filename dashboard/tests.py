from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework import status


class DashboardAccessTests(TestCase):
    def setUp(self):
        self.superuser = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='testpass123',
        )
        self.staff = User.objects.create_user(
            username='staff',
            email='staff@example.com',
            password='testpass123',
            is_staff=True,
        )

    def test_index_redirects_anonymous(self):
        r = self.client.get(reverse('dashboard:index'))
        self.assertEqual(r.status_code, status.HTTP_302_FOUND)
        self.assertIn(reverse('dashboard:login'), r.url)

    def test_index_ok_for_superuser(self):
        self.client.login(username='admin', password='testpass123')
        r = self.client.get(reverse('dashboard:index'))
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_index_forbidden_for_non_superuser(self):
        self.client.login(username='staff', password='testpass123')
        r = self.client.get(reverse('dashboard:index'))
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_login_rejects_non_superuser_credentials(self):
        r = self.client.post(
            reverse('dashboard:login'),
            {'username': 'staff', 'password': 'testpass123'},
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertContains(r, 'superuser', status_code=200)
