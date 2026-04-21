from blacklist.models import GlobalReputationEntry
from rest_framework import serializers
from management.models import Agency
from core_shared.hashing import hash_identity, normalize_identity


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
    cin = serializers.CharField(required=False, allow_blank=True)
    license_number = serializers.CharField(required=False, allow_blank=True)
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
            
        if not attrs.get('cin') and not attrs.get('license_number'):
            raise serializers.ValidationError("Il faut au moins un CIN ou un permis.")
        
        return attrs

    def create(self, validated_data):
        # We hash them here using the Global Salt before saving
        cin_raw = validated_data.get('cin')
        lic_raw = validated_data.get('license_number')
        
        return GlobalReputationEntry.objects.create(
            cin_hash=hash_identity(normalize_identity(cin_raw)) if cin_raw else None,
            license_hash=hash_identity(normalize_identity(lic_raw)) if lic_raw else None,
            reason=validated_data['reason'],
            rating=validated_data['rating'],
            reported_by=validated_data['agency']
        )
