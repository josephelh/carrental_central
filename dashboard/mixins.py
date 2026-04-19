from django.contrib.auth.mixins import UserPassesTestMixin


class SuperuserRequiredMixin(UserPassesTestMixin):
    """Restrict dashboard to Django superusers (central super-admins)."""

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_superuser
