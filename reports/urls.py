from django.urls import path
import reports.views

urlpatterns = [
    path('payroll_summary', reports.views.payroll_summary, name='payroll_summary'),
    path('generate_payroll_pdf', reports.views.generate_payroll_pdf, name='generate_payroll_pdf'),
    path('tax_deduction_report', reports.views.tax_deduction_report, name='tax_deduction_report'),
    path('tax_deduction_report_pdf', reports.views.tax_deduction_report_pdf, name='tax_deduction_report_pdf'),
    path('admin_analytics', reports.views.admin_analytics, name='admin_analytics'),
    path('generate_admin_report_pdf', reports.views.generate_admin_report_pdf, name='generate_admin_report_pdf'),
]