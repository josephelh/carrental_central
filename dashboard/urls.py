from django.urls import path

from . import views

app_name = 'dashboard'

urlpatterns = [
    path('accounts/login/', views.DashboardLoginView.as_view(), name='login'),
    path('accounts/logout/', views.DashboardLogoutView.as_view(), name='logout'),
    path('', views.IndexView.as_view(), name='index'),
    path('agencies/', views.AgencyListView.as_view(), name='agency-list'),
    path('agencies/new/', views.AgencyCreateView.as_view(), name='agency-create'),
    path('agencies/<int:pk>/edit/', views.AgencyUpdateView.as_view(), name='agency-update'),
    path('tiers/', views.TierListView.as_view(), name='tier-list'),
    path('tiers/new/', views.TierCreateView.as_view(), name='tier-create'),
    path('tiers/<int:pk>/edit/', views.TierUpdateView.as_view(), name='tier-update'),
    path('reputation/', views.ReputationListView.as_view(), name='reputation-list'),
    path(
        'reputation/<int:pk>/edit/',
        views.ReputationUpdateView.as_view(),
        name='reputation-update',
    ),
    path(
        'reputation/<int:pk>/delete/',
        views.ReputationDeleteView.as_view(),
        name='reputation-delete',
    ),
]
