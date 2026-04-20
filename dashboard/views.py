from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.views import LoginView, LogoutView
from django.db.models import Avg, Count, Max, OuterRef, Subquery, Sum
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, DeleteView, ListView, TemplateView, UpdateView

from blacklist.models import GlobalReputationEntry
from management.models import Agency, Tier

from .forms import AgencyForm, ReputationForm, TierForm
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
        ctx['recent_reports'] = GlobalReputationEntry.objects.select_related('reported_by').order_by('-created_at')[:10]
        return ctx


class AgencyListView(LoginRequiredMixin, SuperuserRequiredMixin, ListView):
    model = Agency
    template_name = 'dashboard/agency_list.html'
    context_object_name = 'agencies'
    paginate_by = 25
    queryset = Agency.objects.select_related('tier').order_by('name')


class AgencyCreateView(LoginRequiredMixin, SuperuserRequiredMixin, CreateView):
    model = Agency
    form_class = AgencyForm
    template_name = 'dashboard/agency_form.html'

    def form_valid(self, form):
        messages.success(self.request, 'Agency created successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('dashboard:agency-list')


class AgencyUpdateView(LoginRequiredMixin, SuperuserRequiredMixin, UpdateView):
    model = Agency
    form_class = AgencyForm
    template_name = 'dashboard/agency_form.html'
    context_object_name = 'agency'

    def get_queryset(self):
        return Agency.objects.select_related('tier')

    def form_valid(self, form):
        messages.success(self.request, 'Agency updated successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('dashboard:agency-list')


class TierListView(LoginRequiredMixin, SuperuserRequiredMixin, ListView):
    model = Tier
    template_name = 'dashboard/tier_list.html'
    context_object_name = 'tiers'
    queryset = Tier.objects.order_by('name')


class TierCreateView(LoginRequiredMixin, SuperuserRequiredMixin, CreateView):
    model = Tier
    form_class = TierForm
    template_name = 'dashboard/tier_form.html'

    def form_valid(self, form):
        messages.success(self.request, 'Tier created successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('dashboard:tier-list')


class TierUpdateView(LoginRequiredMixin, SuperuserRequiredMixin, UpdateView):
    model = Tier
    form_class = TierForm
    template_name = 'dashboard/tier_form.html'
    context_object_name = 'tier'

    def form_valid(self, form):
        messages.success(self.request, 'Tier updated successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('dashboard:tier-list')


class ReputationListView(LoginRequiredMixin, SuperuserRequiredMixin, ListView):
    model = GlobalReputationEntry
    template_name = 'dashboard/blacklist_list.html'
    context_object_name = 'entries'
    paginate_by = 25

    def get_queryset(self):
        latest_reason_subquery = (
            GlobalReputationEntry.objects.filter(identity_hash=OuterRef('identity_hash'))
            .order_by('-created_at')
            .values('reason')[:1]
        )
        queryset = (
            GlobalReputationEntry.objects.values('identity_hash')
            .annotate(
                avg_rating=Avg('rating'),
                total_reports=Count('id'),
                latest_created_at=Max('created_at'),
                latest_reason=Subquery(latest_reason_subquery),
            )
            .order_by('-latest_created_at')
        )
        self.search_query = self.request.GET.get('q', '').strip()
        if self.search_query:
            queryset = queryset.filter(identity_hash__icontains=self.search_query)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        for entry in context['entries']:
            avg = entry['avg_rating'] or 0
            entry['avg_rating_value'] = float(avg)
            entry['filled_stars'] = range(int(round(avg)))
            entry['empty_stars'] = range(5 - int(round(avg)))
        context['search_query'] = getattr(self, 'search_query', '')
        return context


class ReputationUpdateView(LoginRequiredMixin, SuperuserRequiredMixin, UpdateView):
    model = GlobalReputationEntry
    form_class = ReputationForm
    template_name = 'dashboard/reputation_form.html'
    context_object_name = 'entry'

    def form_valid(self, form):
        messages.success(self.request, 'Reputation entry updated successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('dashboard:reputation-list')


class ReputationDeleteView(LoginRequiredMixin, SuperuserRequiredMixin, DeleteView):
    model = GlobalReputationEntry
    template_name = 'dashboard/reputation_confirm_delete.html'
    context_object_name = 'entry'
    success_url = reverse_lazy('dashboard:reputation-list')

    def form_valid(self, form):
        messages.success(self.request, 'Reputation entry deleted successfully.')
        return super().form_valid(form)
