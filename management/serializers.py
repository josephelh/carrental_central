from rest_framework import serializers


class LicenseVerifySerializer(serializers.Serializer):
    license_key = serializers.UUIDField()
