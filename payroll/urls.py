from django.urls import path
import payroll.views

urlpatterns = [
    path('view_payslips/<int:employee_id>/', payroll.views.view_payslips, name='view_payslips'),
    path('get_pay_salary', payroll.views.get_pay_salary, name='get_pay_salary'),
    path('view_pay_salary', payroll.views.view_pay_salary, name='view_pay_salary'),
    path('edit_common_pay/<int:commonpay_id>/', payroll.views.edit_common_pay, name='edit_common_pay'),
    path('change_pay/<int:commonpay_id>/', payroll.views.change_pay, name='change_pay'),
    path('run_payroll/<int:employee_id>/', payroll.views.run_payroll, name='run_payroll'),
    path('approve_pay/<int:commonpay_id>/', payroll.views.approve_pay, name='approve_pay'),
    path('hr_view_pay', payroll.views.hr_view_pay, name='hr_view_pay'),
    path('generate_payslip_pdf/<int:payslip_id>/', payroll.views.generate_payslip_pdf, name='generate_payslip_pdf'),
    path('views_pay_salary', payroll.views.views_pay_salary, name='views_pay_salary'),
    path('view_payslips', payroll.views.view_payslips, name='view_payslips'),
    path('payment_history', payroll.views.payment_history, name='payment_history'),
    path('views_payslips/<int:employee_id>/', payroll.views.views_payslips, name='views_payslips'),
]