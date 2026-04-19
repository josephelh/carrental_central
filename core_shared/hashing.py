import hashlib
import hmac
import re

from django.conf import settings


def normalize_identity(raw: str) -> str:
    """Collapse whitespace and non-alphanumeric characters; uppercase for stable hashing."""
    collapsed = ''.join(raw.split())
    return re.sub(r'[^A-Za-z0-9]', '', collapsed).upper()


def hash_identity(normalized_identity: str) -> str:
    """
    HMAC-SHA256 hex digest of the normalized CIN or license string using settings.GLOBAL_SALT.
    """
    salt = settings.GLOBAL_SALT
    if not salt:
        raise ValueError('GLOBAL_SALT is not configured.')
    return hmac.new(
        salt.encode('utf-8'),
        normalized_identity.encode('utf-8'),
        hashlib.sha256,
    ).hexdigest()


def hash_cin_or_license(raw: str) -> str:
    """
    Normalize then hash a CIN or license value (convenience for callers with raw input).
    """
    return hash_identity(normalize_identity(raw))
