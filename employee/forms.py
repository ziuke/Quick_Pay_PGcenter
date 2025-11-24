from django import forms
from django.utils import timezone

from employee.models import LeaveRequest, Employee, PerformanceReview
from user.models import User


class LeaveRequestForm(forms.ModelForm):
    class Meta:
        model = LeaveRequest
        exclude = ['status', 'em']
        fields = ['type', 'start_date', 'end_date']
        widgets = {
            'type': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        today = timezone.now().date()

        # Start date cannot be in the past
        if start_date and start_date < today:
            self.add_error('start_date', 'Start date cannot be in the past.')

        # End date cannot be before today
        if end_date and end_date < today:
            self.add_error('end_date', 'End date cannot be in the past.')

        # End date cannot be before start date
        if start_date and end_date and end_date < start_date:
            self.add_error('end_date', 'End date cannot be before start date.')


class AddEmployeeForm(forms.ModelForm):
    user = forms.ModelChoiceField(
        queryset=User.objects.filter(role='employee', is_active=True)
        .exclude(employee_profile__isnull=False),
        label="Select User",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = Employee
        fields = ['user', 'department', 'salary', 'status']
        widgets = {
            'department': forms.Select(attrs={'class': 'form-select'}),
            'salary': forms.NumberInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'})
        }


class EditEmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ['department', 'salary', 'status']
        widgets = {
            'department': forms.Select(attrs={'class': 'form-select'}),
            'salary': forms.NumberInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'})
        }


class PerformanceReviewForm(forms.ModelForm):
    class Meta:
        model = PerformanceReview
        fields = ['rating', 'comments']
        widgets = {
            'comments': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'rating': forms.Select(attrs={'class': 'form-select'}),
        }
