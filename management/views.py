from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core_shared.authentication import InternalSystemTokenAuthentication

from .models import Agency
from .serializers import LicenseVerifySerializer


@api_view(['POST'])
@authentication_classes([InternalSystemTokenAuthentication])
@permission_classes([IsAuthenticated])
def verify_license(request):
    serializer = LicenseVerifySerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    license_key = serializer.validated_data['license_key']
    agency = get_object_or_404(
        Agency.objects.select_related('tier'),
        license_key=license_key,
    )
    return Response(
        {
            'name': agency.name,
            'is_active': agency.is_active,
            'max_cars': agency.tier.max_cars,
        }
    )
