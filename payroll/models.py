from decimal import Decimal

from django.db import models
from django.utils import timezone

from employee.models import Employee


# Create your models here.
class CommonPay(models.Model):
    STATUS = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Edit Requested', 'Edit Requested'),
    ]
    da = models.FloatField(default=0.0, help_text="Dearness Allowance (%)")
    hra = models.FloatField(default=0.0, help_text="House Rent Allowance (%)")
    pf = models.FloatField(default=0.0, help_text="Provident Fund (%)")
    esi = models.FloatField(default=0.0, help_text="Employees State Insurance (%)")
    effective_from = models.DateField(help_text="Date from which these rates are effective")
    created_on = models.DateField(auto_now_add=True)
    updated_on = models.DateField(auto_now=True)
    status = models.CharField(max_length=15, choices=STATUS, default='Pending')

    def __str__(self):
        return f"Common Pay Rules (Effective from {self.effective_from})"


class GrossSalary(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="gross_salaries")
    basic_pay = models.DecimalField(max_digits=10, decimal_places=2)

    # store calculated amounts only
    da_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    hra_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    allowances = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    gross_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)  # pre-calculated

    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(default=timezone.now)

    def __str__(self):
        return f"{self.employee.user.get_username()} ({self.start_date} - {self.end_date})"


PT_SLABS_DICT = [
    (12000, 17999, 320),
    (18000, 29999, 450),
    (30000, 44999, 600),
    (45000, 99999, 750),
    (100000, 124999, 1000),
    (125000, float('inf'), 1250),
]


class TotalDeductions(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="deduction_summary")
    pf = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    esi = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    pt = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    income_tax = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    total_deduction = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    date = models.DateField(auto_now_add=True)
    gross_salary_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    ESI_RATE = Decimal('0.0075')  # 0.75%

    def calculate_pt(self):
        """Calculate PT based on gross salary using slabs"""
        for min_salary, max_salary, slab_amount in PT_SLABS_DICT:
            if min_salary <= self.gross_salary_amount <= max_salary:
                self.pt = slab_amount
                return slab_amount
        self.pt = 0.0
        return 0.0

    def calculate_esi(self):
        """Apply ESI at 0.75% only if gross salary <= ₹21,000"""
        if self.gross_salary_amount <= 21000:
            self.esi = self.gross_salary_amount * self.ESI_RATE
        else:
            self.esi = Decimal('0.0')
        return self.esi

    def calculate_total(self):
        """Calculate total deductions"""
        self.calculate_pt()
        self.calculate_esi()
        self.total_deduction = self.pf + self.esi + self.pt + self.income_tax
        return self.total_deduction

    def save(self, *args, **kwargs):
        self.calculate_total()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.employee.user.get_username()} - {self.date}"


class TaxDeduction(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="tax_deductions")
    deduction_summary = models.ForeignKey(TotalDeductions, on_delete=models.CASCADE, related_name="detailed_deductions")
    tax_amt = models.DecimalField(max_digits=10, decimal_places=2)
    applicable_date = models.DateField()

    def __str__(self):
        return f"{self.tax_type} - {self.tax_amt}"


class Payroll(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="payrolls")
    gross = models.ForeignKey(GrossSalary, on_delete=models.CASCADE)
    deductions = models.ForeignKey(TotalDeductions, on_delete=models.CASCADE)
    net_salary = models.DecimalField(max_digits=10, decimal_places=2)
    bonuses = models.DecimalField(max_digits=10, decimal_places=2, null=True, default=0.0)
    payment_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"Payroll - {self.employee.user.get_username()} ({self.payment_date})"


class Payslip(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="payslips")
    payroll = models.OneToOneField(Payroll, on_delete=models.CASCADE, related_name="payslip")
    total_earnings = models.DecimalField(max_digits=10, decimal_places=2)
    total_deductions = models.DecimalField(max_digits=10, decimal_places=2)
    net_pay = models.DecimalField(max_digits=10, decimal_places=2)
    generated_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"Payslip - {self.employee.user.get_username()} ({self.generated_date})"
