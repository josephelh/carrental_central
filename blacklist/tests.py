from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient

from core_shared.hashing import hash_identity, normalize_identity
from blacklist.models import GlobalReputationEntry
from management.models import Agency, Tier

@override_settings(
    INTERNAL_SYSTEM_TOKEN='test-system-token',
    GLOBAL_SALT='test-global-salt',
)
class BlacklistApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.check_url = '/api/agency/blacklist/check/'
        self.report_url = '/api/agency/blacklist/report/'
        self.tier = Tier.objects.create(name='Small', max_cars=10, price_per_month='99.99')
        self.agency = Agency.objects.create(
            name='Reporter Agency',
            contact_email='rep@example.com',
            subdomain='reporter',
            tier=self.tier,
            is_active=True,
        )
        self.agency_two = Agency.objects.create(
            name='Second Agency',
            contact_email='rep2@example.com',
            subdomain='reporter2',
            tier=self.tier,
            is_active=True,
        )

    def _headers(self, token='test-system-token'):
        return {'HTTP_X_INTERNAL_SYSTEM_TOKEN': token}

    def _report_headers(self, token='test-system-token', license_key=None):
        headers = self._headers(token=token)
        if license_key is not None:
            headers['HTTP_X_LICENSE_KEY'] = str(license_key)
        return headers

    def test_check_returns_empty_aggregate_when_not_listed(self):
        response = self.client.post(
            self.check_url,
            {'id_number': 'AB123456'},
            format='json',
            **self._headers(),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['reputation_score']['total_reports'], 0)
        self.assertIsNone(response.data['reputation_score']['avg_rating'])
        self.assertEqual(response.data['reputation_score']['status'], 'NEUTRAL')
        self.assertEqual(response.data['recent_reasons'], [])

    def test_check_returns_aggregate_after_reports(self):
        self.client.post(
            self.report_url,
            {
                'id_number': 'ab 12-34-56',
                'reason': 'Fraud',
                'rating': 1,
            },
            format='json',
            **self._report_headers(license_key=self.agency.license_key),
        )
        self.client.post(
            self.report_url,
            {
                'id_number': 'ab 12-34-56',
                'reason': 'Non-payment',
                'rating': 3,
            },
            format='json',
            **self._report_headers(license_key=self.agency_two.license_key),
        )
        response = self.client.post(
            self.check_url,
            {'id_number': 'AB123456'},
            format='json',
            **self._headers(),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['reputation_score']['total_reports'], 2)
        self.assertEqual(response.data['reputation_score']['avg_rating'], 2.0)
        self.assertEqual(response.data['reputation_score']['status'], 'DANGER')
        self.assertEqual(response.data['recent_reasons'], ['Non-payment', 'Fraud'])
        self.assertEqual(
            response.data['identity_hash'],
            hash_identity(normalize_identity('AB123456')),
        )

    def test_report_updates_existing_review_for_same_agency_and_identity(self):
        body = {
            'id_number': 'XY999',
            'reason': 'First',
            'rating': 2,
        }
        r1 = self.client.post(
            self.report_url,
            body,
            format='json',
            **self._report_headers(license_key=self.agency.license_key),
        )
        self.assertEqual(r1.status_code, status.HTTP_201_CREATED)
        r2 = self.client.post(
            self.report_url,
            {**body, 'reason': 'Second', 'rating': 1},
            format='json',
            **self._report_headers(license_key=self.agency.license_key),
        )
        self.assertEqual(r2.status_code, status.HTTP_200_OK)
        self.assertEqual(r2.data['rating'], 1)
        self.assertTrue(r2.data['updated_existing'])
        self.assertEqual(
            GlobalReputationEntry.objects.filter(
                identity_hash=hash_identity(normalize_identity('XY999')),
                reported_by=self.agency,
            ).count(),
            1,
        )

    def test_report_inactive_agency_rejected(self):
        self.agency.is_active = False
        self.agency.save(update_fields=['is_active'])
        response = self.client.post(
            self.report_url,
            {
                'id_number': 'ZZ1',
                'reason': 'Test',
                'rating': 3,
            },
            format='json',
            **self._report_headers(license_key=self.agency.license_key),
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_check_marks_blacklisted_when_average_below_two(self):
        self.client.post(
            self.report_url,
            {
                'id_number': 'LM123',
                'reason': 'Accident',
                'rating': 1,
            },
            format='json',
            **self._report_headers(license_key=self.agency.license_key),
        )
        response = self.client.post(
            self.check_url,
            {'id_number': 'LM123'},
            format='json',
            **self._headers(),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['reputation_score']['status'], 'DANGER')

    def test_missing_internal_token_returns_401(self):
        response = self.client.post(
            self.check_url,
            {'id_number': 'AB123456'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @override_settings(GLOBAL_SALT='')
    def test_check_without_salt_config_returns_503(self):
        response = self.client.post(
            self.check_url,
            {'id_number': 'AB123456'},
            format='json',
            **self._headers(),
        )
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)

    def test_report_requires_x_license_key_header(self):
        response = self.client.post(
            self.report_url,
            {'id_number': 'AB123', 'reason': 'Test', 'rating': 2},
            format='json',
            **self._headers(),
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_report_with_invalid_x_license_key_rejected(self):
        response = self.client.post(
            self.report_url,
            {'id_number': 'AB123', 'reason': 'Test', 'rating': 2},
            format='json',
            **self._report_headers(license_key='00000000-0000-0000-0000-000000000000'),
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_id_number_is_required_in_payload(self):
        response = self.client.post(
            self.check_url,
            {'identity': 'AB123456'},
            format='json',
            **self._headers(),
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_hashing_is_deterministic(self):
        n = normalize_identity('  ab-12  ')
        self.assertEqual(n, 'AB12')
        h1 = hash_identity(n)
        h2 = hash_identity(normalize_identity('ab12'))
        self.assertEqual(h1, h2)
