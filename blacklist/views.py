from django.db import IntegrityError
from django.db.models import Avg, Count
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q
from core_shared.authentication import InternalSystemTokenAuthentication
from core_shared.hashing import hash_identity, normalize_identity

from .models import GlobalReputationEntry
from .serializers import BlacklistCheckSerializer, BlacklistReportSerializer

class ReputationCheckView(APIView):
    authentication_classes = [InternalSystemTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = BlacklistCheckSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # 1. Normalize and Hash the searched ID
        normalized_search_id = serializer.validated_data['identity']
        try:
            digest = hash_identity(normalized_search_id)
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        # 2. CROSS-LINKING QUERY
        # We look for any record where the digest matches EITHER the stored CIN OR the stored License.
        entries = GlobalReputationEntry.objects.filter(
            Q(cin_hash=digest) | Q(license_hash=digest)
        ).select_related('reported_by')

        # 3. STATS AGGREGATION
        stats = entries.aggregate(avg=Avg('rating'), count=Count('id'))
        
        avg_rating = stats['avg'] or 0
        total_reports = stats['count']

        # 4. HYBRID STATUS LOGIC
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
    """
    Creates a new reputation entry.
    Accepts 'cin' and 'license_number' to link them in the global database.
    """
    authentication_classes = [InternalSystemTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = BlacklistReportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # 1. Get raw values from request (hashed server-side with GLOBAL_SALT)
        raw_cin = request.data.get('cin')
        raw_license = request.data.get('license_number')
        
        cin_digest = hash_identity(normalize_identity(raw_cin)) if raw_cin else None
        license_digest = hash_identity(normalize_identity(raw_license)) if raw_license else None
        
        if not cin_digest and not license_digest:
            return Response(
                {"detail": "Au moins un identifiant (CIN ou Permis) est requis pour le signalement."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        agency = serializer.validated_data['agency']
        
        try:
            # 2. Create the linked entry
            entry = GlobalReputationEntry.objects.create(
                cin_hash=cin_digest,
                license_hash=license_digest,
                reason=serializer.validated_data['reason'],
                rating=serializer.validated_data['rating'],
                reported_by=agency
            )
            return Response({"status": "success", "id": entry.id}, status=status.HTTP_201_CREATED)
            
        except IntegrityError:
            return Response(
                {"detail": "Ce client a déjà été signalé par votre agence."}, 
                status=status.HTTP_409_CONFLICT
            )