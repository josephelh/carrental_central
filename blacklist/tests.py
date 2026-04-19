from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient

from core_shared.hashing import hash_identity, normalize_identity
from management.models import Agency, Tier

from .models import Severity


@override_settings(
    INTERNAL_SYSTEM_TOKEN='test-system-token',
    GLOBAL_SALT='test-global-salt',
)
class BlacklistApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.check_url = '/api/agency/blacklist/check/'
        self.report_url = '/api/agency/blacklist/report/'
        self.tier = Tier.objects.get(name='Small')
        self.agency = Agency.objects.create(
            name='Reporter Agency',
            contact_email='rep@example.com',
            subdomain='reporter',
            tier=self.tier,
            is_active=True,
        )

    def _headers(self, token='test-system-token'):
        return {'HTTP_X_INTERNAL_SYSTEM_TOKEN': token}

    def test_check_returns_empty_matches_when_not_listed(self):
        response = self.client.post(
            self.check_url,
            {'identity': 'AB123456'},
            format='json',
            **self._headers(),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['matches'], [])

    def test_check_returns_match_after_report(self):
        self.client.post(
            self.report_url,
            {
                'identity': 'ab 12-34-56',
                'reason': 'Fraud',
                'license_key': str(self.agency.license_key),
                'severity': Severity.HIGH,
            },
            format='json',
            **self._headers(),
        )
        response = self.client.post(
            self.check_url,
            {'identity': 'AB123456'},
            format='json',
            **self._headers(),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['matches']), 1)
        m = response.data['matches'][0]
        self.assertEqual(m['reason'], 'Fraud')
        self.assertEqual(m['severity'], Severity.HIGH)
        self.assertEqual(m['reported_by_agency'], 'Reporter Agency')

    def test_report_duplicate_returns_409(self):
        body = {
            'identity': 'XY999',
            'reason': 'First',
            'license_key': str(self.agency.license_key),
        }
        r1 = self.client.post(
            self.report_url,
            body,
            format='json',
            **self._headers(),
        )
        self.assertEqual(r1.status_code, status.HTTP_201_CREATED)
        r2 = self.client.post(
            self.report_url,
            {**body, 'reason': 'Second'},
            format='json',
            **self._headers(),
        )
        self.assertEqual(r2.status_code, status.HTTP_409_CONFLICT)

    def test_report_inactive_agency_rejected(self):
        self.agency.is_active = False
        self.agency.save(update_fields=['is_active'])
        response = self.client.post(
            self.report_url,
            {
                'identity': 'ZZ1',
                'reason': 'Test',
                'license_key': str(self.agency.license_key),
            },
            format='json',
            **self._headers(),
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_internal_token_returns_401(self):
        response = self.client.post(
            self.check_url,
            {'identity': 'AB123456'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @override_settings(GLOBAL_SALT='')
    def test_check_without_salt_config_returns_503(self):
        response = self.client.post(
            self.check_url,
            {'identity': 'AB123456'},
            format='json',
            **self._headers(),
        )
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)

    def test_hashing_is_deterministic(self):
        n = normalize_identity('  ab-12  ')
        self.assertEqual(n, 'AB12')
        h1 = hash_identity(n)
        h2 = hash_identity(normalize_identity('ab12'))
        self.assertEqual(h1, h2)
