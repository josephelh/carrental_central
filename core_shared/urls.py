from django.urls import path

from blacklist.views import reputation_check, reputation_report
from management.views import verify_license

urlpatterns = [
    path('verify/', verify_license, name='agency-verify-license'),
    path('reputation/check/', reputation_check, name='agency-reputation-check'),
    path('reputation/report/', reputation_report, name='agency-reputation-report'),
]
