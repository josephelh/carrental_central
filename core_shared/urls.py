from django.urls import path

from blacklist.views import BlacklistCheckView, BlacklistReportView
from management.views import VerifyLicenseView

urlpatterns = [
    path('verify_license/', VerifyLicenseView.as_view(), name='agency-verify-license'),
    path('blacklist/check/', BlacklistCheckView.as_view(), name='agency-blacklist-check'),
    path('blacklist/report/', BlacklistReportView.as_view(), name='agency-blacklist-report'),
]
