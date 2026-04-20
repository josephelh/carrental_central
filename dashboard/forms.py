from django import forms

from blacklist.models import GlobalReputationEntry
from management.models import Agency, Tier

INPUT_CLASSES = (
    'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg '
    'focus:ring-blue-600 focus:border-blue-600 block w-full p-2.5 '
    'dark:bg-gray-700 dark:border-gray-600 dark:text-white '
    'dark:focus:ring-blue-500 dark:focus:border-blue-500'
)


class AgencyForm(forms.ModelForm):
    class Meta:
        model = Agency
        fields = ['name', 'contact_email', 'subdomain', 'tier', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': INPUT_CLASSES}),
            'contact_email': forms.EmailInput(attrs={'class': INPUT_CLASSES}),
            'subdomain': forms.TextInput(attrs={'class': INPUT_CLASSES}),
            'tier': forms.Select(attrs={'class': INPUT_CLASSES}),
            'is_active': forms.CheckboxInput(
                attrs={
                    'class': (
                        'h-4 w-4 rounded border-gray-300 text-blue-600 '
                        'focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700'
                    )
                }
            ),
        }


class ReputationForm(forms.ModelForm):
    class Meta:
        model = GlobalReputationEntry
        fields = ['reason', 'rating']
        widgets = {
            'reason': forms.Textarea(attrs={'class': INPUT_CLASSES, 'rows': 4}),
            'rating': forms.NumberInput(attrs={'class': INPUT_CLASSES, 'min': 1, 'max': 5}),
        }


class TierForm(forms.ModelForm):
    class Meta:
        model = Tier
        fields = ['name', 'max_cars', 'price_per_month']
        widgets = {
            'name': forms.TextInput(attrs={'class': INPUT_CLASSES}),
            'max_cars': forms.NumberInput(attrs={'class': INPUT_CLASSES, 'min': 1}),
            'price_per_month': forms.NumberInput(
                attrs={'class': INPUT_CLASSES, 'step': '0.01', 'min': '0'}
            ),
        }
