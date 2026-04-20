from rest_framework import serializers
from management.models import Agency
from core_shared.hashing import normalize_identity


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
    identity = serializers.CharField()
    reason = serializers.CharField()
    rating = serializers.IntegerField(min_value=1, max_value=5)
    license_key = serializers.UUIDField()

    def validate_identity(self, value):
        return _clean_identity(value)

    def validate(self, attrs):
        # This method is CRITICAL. It checks if the agency exists and is active.
        license_key = attrs.get('license_key')
        try:
            agency = Agency.objects.get(license_key=license_key)
        except Agency.DoesNotExist:
            raise serializers.ValidationError({"license_key": "Invalid agency license key."})
        
        if not agency.is_active:
            raise serializers.ValidationError({"license_key": "This agency is currently inactive."})
            
        # Add the actual agency object to the validated data for the view to use
        attrs['agency'] = agency
        return attrs
