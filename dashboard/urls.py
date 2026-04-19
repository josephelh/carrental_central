from django.urls import path

from . import views

app_name = 'dashboard'

urlpatterns = [
    path('accounts/login/', views.DashboardLoginView.as_view(), name='login'),
    path('accounts/logout/', views.DashboardLogoutView.as_view(), name='logout'),
    path('', views.IndexView.as_view(), name='index'),
    path('agencies/', views.AgencyListView.as_view(), name='agency-list'),
    path('agencies/<int:pk>/', views.AgencyDetailView.as_view(), name='agency-detail'),
    path('blacklist/', views.BlacklistListView.as_view(), name='blacklist-list'),
]
