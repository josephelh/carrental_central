import uuid

from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient

from .models import Agency, Tier


@override_settings(INTERNAL_SYSTEM_TOKEN='test-system-token')
class VerifyLicenseApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = '/api/agency/verify_license/'
        self.tier = Tier.objects.get(name='Small')
        self.agency = Agency.objects.create(
            name='Test Rentals',
            contact_email='ops@test.example',
            subdomain='test-rentals',
            tier=self.tier,
            is_active=True,
        )

    def _headers(self, token='test-system-token'):
        return {'HTTP_X_INTERNAL_SYSTEM_TOKEN': token}

    def test_success_returns_agency_and_tier_max_cars(self):
        response = self.client.post(
            self.url,
            {'license_key': str(self.agency.license_key)},
            format='json',
            **self._headers(),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data,
            {
                'name': 'Test Rentals',
                'is_active': True,
                'max_cars': self.tier.max_cars,
            },
        )

    def test_missing_internal_token_returns_401(self):
        response = self.client.post(
            self.url,
            {'license_key': str(self.agency.license_key)},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_wrong_internal_token_returns_401(self):
        response = self.client.post(
            self.url,
            {'license_key': str(self.agency.license_key)},
            format='json',
            **self._headers('wrong-token'),
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unknown_license_returns_404(self):
        response = self.client.post(
            self.url,
            {'license_key': str(uuid.uuid4())},
            format='json',
            **self._headers(),
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @override_settings(INTERNAL_SYSTEM_TOKEN='')
    def test_empty_configured_token_returns_401(self):
        response = self.client.post(
            self.url,
            {'license_key': str(self.agency.license_key)},
            format='json',
            **self._headers(''),
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
