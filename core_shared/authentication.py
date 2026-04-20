import hmac
from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth.models import User

class InternalSystemTokenAuthentication(BaseAuthentication):
    def authenticate(self, request):
        expected_token = getattr(settings, "INTERNAL_SYSTEM_TOKEN", "").strip()
        
        if not expected_token:
            print("🚨 CENTRAL ERROR: INTERNAL_SYSTEM_TOKEN is empty in settings!")
            raise AuthenticationFailed('Server configuration error.')

        # Django transforms headers: X-Internal-System-Token -> HTTP_X_INTERNAL_SYSTEM_TOKEN
        provided_token = request.META.get('HTTP_X_INTERNAL_SYSTEM_TOKEN', '').strip()

        if not provided_token:
            print("🚨 CENTRAL AUTH: No token provided in request header 'X-Internal-System-Token'.")
            raise AuthenticationFailed('No system token provided.')

        if not hmac.compare_digest(provided_token, expected_token):
            print("🚨 CENTRAL AUTH: TOKEN MISMATCH!")
            print(f"   Received: [{provided_token}] (Len: {len(provided_token)})")
            print(f"   Expected: [{expected_token}] (Len: {len(expected_token)})")
            raise AuthenticationFailed('Invalid system token.')

        # Authenticate as the first superuser so the request has permissions
        user = User.objects.filter(is_superuser=True).first()
        if not user:
            print("🚨 CENTRAL ERROR: No superuser found in database to associate with bridge call!")
            raise AuthenticationFailed('No admin user configured.')
            
        return (user, None)

    def authenticate_header(self, request):
        return 'X-Internal-System-Token'