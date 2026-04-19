from rest_framework import serializers

from core_shared.hashing import normalize_identity
from management.models import Agency
from .models import Severity


def _clean_identity(value: str) -> str:
    normalized = normalize_identity(value)
    if not normalized:
        raise serializers.ValidationError('Identity must contain at least one letter or digit.')
    return normalized


class BlacklistCheckSerializer(serializers.Serializer):
    identity = serializers.CharField(trim_whitespace=False)

    def validate_identity(self, value):
        return _clean_identity(value)


class BlacklistReportSerializer(serializers.Serializer):
    identity = serializers.CharField(trim_whitespace=False)
    reason = serializers.CharField(allow_blank=False)
    license_key = serializers.UUIDField()
    severity = serializers.ChoiceField(choices=Severity.choices, default=Severity.MEDIUM)

    def validate_identity(self, value):
        return _clean_identity(value)

    def validate(self, attrs):
        license_key = attrs['license_key']
        try:
            agency = Agency.objects.get(license_key=license_key)
        except Agency.DoesNotExist as exc:
            raise serializers.ValidationError(
                {'license_key': 'Unknown or invalid agency license.'}
            ) from exc
        if not agency.is_active:
            raise serializers.ValidationError(
                {'license_key': 'Agency is not active.'}
            )
        attrs['agency'] = agency
        return attrs
