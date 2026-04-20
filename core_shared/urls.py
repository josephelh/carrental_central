from django.urls import path
from blacklist.views import ReputationCheckView, ReputationReportView
from management.views import VerifyLicenseView

urlpatterns = [
    path('verify/', VerifyLicenseView.as_view(), name='agency-verify-license'),
    path('reputation/check/', ReputationCheckView.as_view(), name='agency-reputation-check'),
    path('reputation/report/', ReputationReportView.as_view(), name='agency-reputation-report'),
]