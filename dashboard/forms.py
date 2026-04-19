from django import forms

from management.models import Agency


class AgencyTierForm(forms.ModelForm):
    class Meta:
        model = Agency
        fields = ['tier']
        widgets = {
            'tier': forms.Select(
                attrs={
                    'class': (
                        'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg '
                        'focus:ring-blue-600 focus:border-blue-600 block w-full p-2.5 '
                        'dark:bg-gray-700 dark:border-gray-600 dark:text-white '
                        'dark:focus:ring-blue-500 dark:focus:border-blue-500'
                    )
                }
            ),
        }
