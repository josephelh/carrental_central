import hashlib
import hmac

from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed


class _BridgePrincipal:
    is_authenticated = True


class InternalSystemTokenAuthentication(BaseAuthentication):
    """
    Authenticates agency bridge calls via X-Internal-System-Token matching
    settings.INTERNAL_SYSTEM_TOKEN.
    """

    def authenticate(self, request):
        expected = settings.INTERNAL_SYSTEM_TOKEN
        if not expected:
            raise AuthenticationFailed('Internal system token is not configured.')

        provided = request.META.get('HTTP_X_INTERNAL_SYSTEM_TOKEN', '')
        e_digest = hashlib.sha256(expected.encode('utf-8')).digest()
        p_digest = hashlib.sha256(provided.encode('utf-8')).digest()
        if not hmac.compare_digest(e_digest, p_digest):
            raise AuthenticationFailed('Invalid internal system token.')
        return (_BridgePrincipal(), None)

    def authenticate_header(self, request):
        return 'X-Internal-System-Token'
