from django.db.models import Avg, Count

from .models import GlobalReputationEntry


def get_reputation_score(id_hash: str) -> dict[str, float | int | str | None]:
    aggregate = GlobalReputationEntry.objects.filter(identity_hash=id_hash).aggregate(
        avg_rating=Avg('rating'),
        total_reports=Count('id'),
    )
    total_reports = aggregate['total_reports'] or 0
    avg = aggregate['avg_rating']
    avg_rating = float(avg) if avg is not None else None

    if total_reports == 0:
        status = 'NEUTRAL'
    elif avg_rating is not None and avg_rating > 4.0:
        status = 'TRUSTED'
    elif avg_rating is not None and avg_rating < 2.5:
        status = 'DANGER'
    else:
        status = 'CAUTION'

    return {
        'avg_rating': avg_rating,
        'total_reports': total_reports,
        'status': status,
    }
