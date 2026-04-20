from django.db import IntegrityError
from django.db.models import Avg, Count
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core_shared.authentication import InternalSystemTokenAuthentication
from core_shared.hashing import hash_identity

from .models import GlobalReputationEntry
from .serializers import BlacklistCheckSerializer, BlacklistReportSerializer

class ReputationCheckView(APIView):
    authentication_classes = [InternalSystemTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = BlacklistCheckSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        normalized = serializer.validated_data['identity']
        
        try:
            digest = hash_identity(normalized)
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        entries = GlobalReputationEntry.objects.filter(identity_hash=digest).select_related('reported_by')
        stats = entries.aggregate(avg=Avg('rating'), count=Count('id'))
        
        avg_rating = stats['avg'] or 0
        total_reports = stats['count']

        status_label = "NEUTRAL"
        is_blacklisted = False
        if total_reports > 0:
            if avg_rating < 2.5:
                status_label = "DANGER"
                is_blacklisted = True
            elif avg_rating < 4.0:
                status_label = "CAUTION"
            else:
                status_label = "TRUSTED"

        return Response({
            "is_blacklisted": is_blacklisted,
            "status": status_label,
            "average_rating": round(float(avg_rating), 1),
            "total_reports": total_reports,
            "recent_reasons": list(entries.values_list('reason', flat=True)[:5]),
            "reporting_agencies": list(entries.values_list('reported_by__name', flat=True))
        })

class ReputationReportView(APIView):
    authentication_classes = [InternalSystemTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = BlacklistReportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        normalized = serializer.validated_data['identity']
        digest = hash_identity(normalized)
        agency = serializer.validated_data['agency'] # From the validate() method above
        
        entry = GlobalReputationEntry.objects.create(
            identity_hash=digest,
            reason=serializer.validated_data['reason'],
            rating=serializer.validated_data['rating'],
            reported_by=agency
        )
        return Response({"status": "success"}, status=status.HTTP_201_CREATED)