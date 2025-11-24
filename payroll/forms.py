from decimal import Decimal

from django import forms

from payroll.models import GrossSalary, CommonPay, TaxDeduction


class GetPayElementsForm(forms.ModelForm):
    class Meta:
        model = CommonPay
        fields = ['hra', 'da', 'pf', 'esi', 'effective_from']
        widgets = {
            'hra': forms.NumberInput(attrs={'class': 'form-control'}),
            'da': forms.NumberInput(attrs={'class': 'form-control'}),
            'pf': forms.NumberInput(attrs={'class': 'form-control'}),
            'esi': forms.NumberInput(attrs={'class': 'form-control'}),
            'effective_from': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class EditCommonPayForm(forms.ModelForm):
    class Meta:
        model = CommonPay
        fields = ['hra', 'da', 'pf', 'esi', 'effective_from']
        widgets = {
            'hra': forms.NumberInput(attrs={'class': 'form-control'}),
            'da': forms.NumberInput(attrs={'class': 'form-control'}),
            'pf': forms.NumberInput(attrs={'class': 'form-control'}),
            'esi': forms.NumberInput(attrs={'class': 'form-control'}),
            'effective_from': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class PayrollManagerForm(forms.Form):
    other_allowances = forms.DecimalField(
        max_digits=10, decimal_places=2,
        required=False, initial=Decimal(0.0),
        label="Other Allowances"
    )
    tax_amt = forms.DecimalField(
        max_digits=10, decimal_places=2,
        label="Tax Amount",
        initial=Decimal(0.0)
    )