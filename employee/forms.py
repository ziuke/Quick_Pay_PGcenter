from django import forms

from employee.models import LeaveRequest, Employee, PerformanceReview
from user.models import User


class LeaveRequestForm(forms.ModelForm):
    class Meta:
        model = LeaveRequest
        exclude = ['status', 'em']
        fields = [
            'type', 'start_date', 'end_date'
        ]
        widgets = {
            'type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control', 'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control', 'type': 'date'
            }),
        }


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
        fields = ['employee', 'rating', 'comments', 'increment_percentage']
        widgets = {
            'comments': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'employee': forms.Select(attrs={'class': 'form-select'}),
            'rating': forms.Select(attrs={'class': 'form-select'}),
            'increment_percentage': forms.NumberInput(attrs={'class': 'form-control'}),
        }
