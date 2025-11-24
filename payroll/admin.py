from django.contrib import admin

from payroll.models import Payroll, Payslip, TaxDeduction

# Register your models here.
admin.site.register(Payroll)
admin.site.register(Payslip)
admin.site.register(TaxDeduction)

