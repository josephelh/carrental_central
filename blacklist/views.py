from django.db import IntegrityError
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core_shared.authentication import InternalSystemTokenAuthentication
from core_shared.hashing import hash_identity

from .models import GlobalBlacklistEntry
from .serializers import BlacklistCheckSerializer, BlacklistReportSerializer


class BlacklistCheckView(APIView):
    authentication_classes = [InternalSystemTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = BlacklistCheckSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        normalized = serializer.validated_data['identity']
        try:
            digest = hash_identity(normalized)
        except ValueError as exc:
            return Response(
                {'detail': str(exc)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        entries = GlobalBlacklistEntry.objects.filter(identity_hash=digest).select_related(
            'reported_by'
        )
        matches = [
            {
                'reason': e.reason,
                'severity': e.severity,
                'created_at': e.created_at,
                'reported_by_agency': e.reported_by.name,
            }
            for e in entries
        ]
        return Response({'matches': matches})


class BlacklistReportView(APIView):
    authentication_classes = [InternalSystemTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = BlacklistReportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        normalized = serializer.validated_data['identity']
        try:
            digest = hash_identity(normalized)
        except ValueError as exc:
            return Response(
                {'detail': str(exc)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        agency = serializer.validated_data['agency']
        try:
            entry = GlobalBlacklistEntry.objects.create(
                identity_hash=digest,
                reason=serializer.validated_data['reason'],
                reported_by=agency,
                severity=serializer.validated_data['severity'],
            )
        except IntegrityError:
            return Response(
                {'detail': 'This identity is already on the global blacklist.'},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(
            {
                'identity_hash': entry.identity_hash,
                'severity': entry.severity,
                'created_at': entry.created_at,
            },
            status=status.HTTP_201_CREATED,
        )
