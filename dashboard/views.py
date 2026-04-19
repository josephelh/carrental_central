from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.views import LoginView, LogoutView
from django.db.models import Sum
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, TemplateView, UpdateView

from blacklist.models import GlobalBlacklistEntry
from management.models import Agency

from .forms import AgencyTierForm
from .mixins import SuperuserRequiredMixin


class DashboardLoginView(LoginView):
    template_name = 'dashboard/login.html'
    redirect_authenticated_user = False

    def form_valid(self, form):
        user = form.get_user()
        if not user.is_superuser:
            form.add_error(
                None,
                'Only Django superuser accounts may access Fleet Central.',
            )
            return self.form_invalid(form)
        return super().form_valid(form)


class DashboardLogoutView(LogoutView):
    next_page = reverse_lazy('dashboard:login')


class IndexView(LoginRequiredMixin, SuperuserRequiredMixin, TemplateView):
    template_name = 'dashboard/index.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['agency_count'] = Agency.objects.count()
        ctx['active_agency_count'] = Agency.objects.filter(is_active=True).count()
        total = (
            Agency.objects.filter(is_active=True).aggregate(s=Sum('tier__price_per_month'))['s']
        )
        ctx['total_revenue_mrr'] = total if total is not None else Decimal('0')
        ctx['recent_reports'] = (
            GlobalBlacklistEntry.objects.select_related('reported_by')
            .order_by('-created_at')[:10]
        )
        return ctx


class AgencyListView(LoginRequiredMixin, SuperuserRequiredMixin, ListView):
    model = Agency
    template_name = 'dashboard/agency_list.html'
    context_object_name = 'agencies'
    paginate_by = 25
    queryset = Agency.objects.select_related('tier').order_by('name')


class AgencyDetailView(LoginRequiredMixin, SuperuserRequiredMixin, UpdateView):
    model = Agency
    form_class = AgencyTierForm
    template_name = 'dashboard/agency_detail.html'
    context_object_name = 'agency'

    def get_queryset(self):
        return Agency.objects.select_related('tier')

    def form_valid(self, form):
        messages.success(self.request, 'Tier updated successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('dashboard:agency-detail', kwargs={'pk': self.object.pk})


class BlacklistListView(LoginRequiredMixin, SuperuserRequiredMixin, ListView):
    model = GlobalBlacklistEntry
    template_name = 'dashboard/blacklist_list.html'
    context_object_name = 'entries'
    paginate_by = 25
    queryset = GlobalBlacklistEntry.objects.select_related('reported_by').order_by('-created_at')
