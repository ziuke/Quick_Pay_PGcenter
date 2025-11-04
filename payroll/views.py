from datetime import date
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.models import Group
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from employee.models import Employee, LeaveRequest, PerformanceReview
from payroll.forms import GetPayElementsForm, EditCommonPayForm, PayrollManagerForm
from payroll.models import Payslip, CommonPay, Payroll, GrossSalary, TotalDeductions, TaxDeduction
from user.models import Notification
from user.views import create_notification


# Create your views here.

def get_pay_salary(request):
    if request.method == 'POST':
        form = GetPayElementsForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Common allowances, tax and deduction details added successfully!")
            create_notification(
                roles=['hr_manager', 'payroll_manager'],
                message=f"Common allowances, taxes and deductions according to government has been added "
            )
            return redirect('view_pay_salary')
    else:
        form = GetPayElementsForm()
    return render(request, 'get_pay_salary.html', {'form': form})


def view_pay_salary(request):
    cp = CommonPay.objects.order_by('-updated_on').first()
    return render(request, 'view_pay_salary.html', {'cp': cp})


def edit_common_pay(request, commonpay_id):
    common_pay = get_object_or_404(CommonPay, id=commonpay_id)
    if request.method == 'POST':
        form = EditCommonPayForm(request.POST, instance=common_pay)
        if form.is_valid():
            form.save()
            create_notification(
                roles=['hr_manager', 'payroll_manager'],
                message=f"Admin has edited common allowances, taxes and deductions."
            )
            messages.success(request, "Common allowances, taxes and deductions updated successfully.")
            return redirect('view_pay_salary')
    else:
        form = EditCommonPayForm(instance=common_pay)
    return render(request, 'edit_common_pay.html', {'form': form})


def hr_view_pay(request):
    cp = CommonPay.objects.order_by('-updated_on').first()
    return render(request, 'hr_view_pay.html', {'cp': cp})


def approve_pay(request, commonpay_id):
    common_pay = get_object_or_404(CommonPay, id=commonpay_id)
    common_pay.status = 'Approved'
    common_pay.save()
    create_notification(
        role='admin',
        message=f"Common allowances, taxes and deductions are approved by the HR Manager"
    )
    messages.success(request, f"Common Pay effective from {common_pay.effective_from} has been approved.")
    return redirect('hr_view_pay')


def change_pay(request, commonpay_id):
    common_pay = get_object_or_404(CommonPay, id=commonpay_id)
    if request.method == 'POST':
        reason = request.POST.get('reason', '').strip()
        if not reason:
            messages.error(request, "Please provide a reason for the change request.")
            return render(request, 'change_pay.html', {'common_pay': common_pay})
        common_pay.status = 'Edit Requested'
        common_pay.save()
        admin_group = Group.objects.filter(name='Admin').first()
        payroll_group = Group.objects.filter(name='Payroll Manager').first()
        recipients = []
        if admin_group:
            recipients += list(admin_group.user_set.all())
        if payroll_group:
            recipients += list(payroll_group.user_set.all())
        for user in recipients:
            create_notification(
                role='admin',
                message=(
                    f"HR has requested a change for Common Pay (Effective from {common_pay.effective_from}). "
                    f"Reason: {reason}"
                )
            )
        messages.success(
            request,
            f"Change request sent for {common_pay.effective_from} with reason: {reason}"
        )
        return redirect('hr_view_pay')
    return render(request, 'change_pay.html', {'common_pay': common_pay})


def run_payroll(request, employee_id):
    employee = get_object_or_404(Employee, id=employee_id)
    today = date.today()

    common_pay = CommonPay.objects.filter(status='Approved').order_by('-effective_from').first()
    if not common_pay:
        messages.error(request, "No approved Common Pay rules available.")
        return redirect('view_employees')

    unpaid_leaves = LeaveRequest.objects.filter(
        em=employee,
        status='approved',
        type='unpaid',
        start_date__month=today.month,
        start_date__year=today.year
    )
    unpaid_days = sum((leave.end_date - leave.start_date).days + 1 for leave in unpaid_leaves)
    total_days = 30
    per_day_salary = employee.salary / total_days if employee.salary else 0

    latest_review = (
        PerformanceReview.objects.filter(employee=employee)
        .order_by('-review_date')
        .first()
    )

    if latest_review:
        performance_bonus = (employee.salary * latest_review.increment_percentage) / 100
    else:
        performance_bonus = Decimal(0.0)

    if request.method == 'POST':
        form = PayrollManagerForm(request.POST)
        if form.is_valid():
            basic_pay = employee.salary
            other_allowances = form.cleaned_data.get('other_allowances') or Decimal(0.0)
            tax_type = form.cleaned_data.get('tax_type')
            tax_amt = form.cleaned_data.get('tax_amt') or Decimal(0.0)

            da_amount = basic_pay * Decimal(common_pay.da / 100)
            hra_amount = basic_pay * Decimal(common_pay.hra / 100)
            gross_total = basic_pay + da_amount + hra_amount + other_allowances + performance_bonus

            gross_record = GrossSalary.objects.create(
                employee=employee,
                basic_pay=basic_pay,
                da_amount=da_amount,
                hra_amount=hra_amount,
                allowances=da_amount + hra_amount + other_allowances + performance_bonus,
                gross_total=gross_total
            )

            pf_amount = basic_pay * Decimal(common_pay.pf / 100)
            esi_amount = gross_total * Decimal(common_pay.esi / 100) if gross_total <= 21000 else Decimal(0.0)
            leave_deduction = unpaid_days * per_day_salary

            td = TotalDeductions.objects.create(
                employee=employee,
                pf=pf_amount,
                esi=esi_amount,
                income_tax=tax_amt if tax_type == 'income_tax' else Decimal(0.0),
                gross_salary_amount=gross_total
            )

            if tax_amt > 0:
                TaxDeduction.objects.create(
                    employee=employee,
                    deduction_summary=td,
                    tax_type=tax_type,
                    tax_amt=tax_amt,
                    applicable_date=today
                )

            td.total_deduction += leave_deduction
            td.save()

            net_salary = gross_total - td.total_deduction

            payroll_record = Payroll.objects.create(
                employee=employee,
                gross=gross_record,
                deductions=td,
                net_salary=net_salary,
                bonuses=performance_bonus
            )

            Payslip.objects.create(
                employee=employee,
                payroll=payroll_record,
                total_earnings=gross_total,
                total_deductions=td.total_deduction,
                net_pay=net_salary
            )

            create_notification(
                user=employee.user,
                message=f"Your payslip for {today.strftime('%B %Y')} has been processed successfully. "
                        f"Net Pay: ₹{net_salary}"
            )
            create_notification(
                role='hr_manager',
                message=f"Payslip for employee ID {employee_id} has been generated."
            )

            messages.success(
                request,
                f"Payroll generated for {employee.user.get_username()} | Unpaid leaves: {unpaid_days}"
            )
            return redirect('view_payslips', employee_id=employee.id)

    else:
        form = PayrollManagerForm()

    summary = {
        'unpaid_days': unpaid_days,
        'per_day_salary': per_day_salary,
    }

    return render(request, 'payroll_entry.html', {
        'form': form,
        'employee': employee,
        'common_pay': common_pay,
        'summary': summary,
        'performance_bonus': performance_bonus,
    })


def view_payslips(request):
    em = request.user
    pay = Payslip.objects.filter(employee_id=em).order_by('-generated_date')
    return render(request, 'view_payslips.html', {'pay': pay})


"""def view_payroll_summary(request):
    payrolls = Payroll.objects.select_related('employee', 'gross', 'deductions').order_by('-payment_date')
    return render(request, 'view_payroll_summary.html', {'payrolls': payrolls})
"""


def generate_payslip_pdf(request, payslip_id):
    payslip = get_object_or_404(Payslip, id=payslip_id)
    payroll = payslip.payroll
    employee = payslip.employee
    gross = payroll.gross
    deductions = payroll.deductions
    if not (request.user.is_superuser or request.user == employee.user):
        return HttpResponse("Unauthorized", status=403)
    response = HttpResponse(content_type='application/pdf')
    response[
        'Content-Disposition'] = f'attachment; filename="Payslip_{employee.user.username}_{payslip.generated_date}.pdf"'
    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4
    p.setFont("Helvetica-Bold", 18)
    p.drawCentredString(width / 2, height - 80, "Company Name Pvt. Ltd.")
    p.setFont("Helvetica", 12)
    p.drawCentredString(width / 2, height - 100, "Employee Payslip")
    y = height - 150
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "Employee Details")
    p.setFont("Helvetica", 10)
    y -= 20
    p.drawString(70, y, f"Name: {employee.user.get_full_name() or employee.user.username}")
    y -= 15
    p.drawString(70, y, f"Department: {getattr(employee, 'department', 'N/A')}")
    y -= 15
    p.drawString(70, y, f"Date: {payslip.generated_date.strftime('%d-%m-%Y')}")
    y -= 40
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "Earnings")
    p.setFont("Helvetica", 10)
    y -= 20
    p.drawString(70, y, f"Basic Pay: ₹{gross.basic_pay}")
    y -= 15
    p.drawString(70, y, f"DA: ₹{gross.da_amount}")
    y -= 15
    p.drawString(70, y, f"HRA: ₹{gross.hra_amount}")
    y -= 15
    p.drawString(70, y, f"Other Allowances: ₹{gross.allowances or 0}")
    y -= 15
    p.drawString(70, y, f"Bonuses: ₹{payroll.bonuses or 0}")
    y -= 40
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "Deductions")
    p.setFont("Helvetica", 10)
    y -= 20
    p.drawString(70, y, f"PF: ₹{deductions.pf}")
    y -= 15
    p.drawString(70, y, f"ESI: ₹{deductions.esi}")
    y -= 15
    p.drawString(70, y, f"PT: ₹{deductions.pt}")
    y -= 15
    p.drawString(70, y, f"Income Tax: ₹{deductions.income_tax}")
    y -= 15
    p.drawString(70, y, f"Total Deductions: ₹{deductions.total_deduction}")
    y -= 40
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "Net Pay")
    p.setFont("Helvetica", 11)
    y -= 20
    p.drawString(70, y, f"₹{payslip.net_pay}")
    p.setFont("Helvetica-Oblique", 9)
    p.drawCentredString(width / 2, 60, "This is a system-generated payslip and does not require a signature.")

    p.showPage()
    p.save()
    messages.success(
        request,
        f"Payslip downloaded successfully."
    )
    return response


def views_pay_salary(request):
    cp = CommonPay.objects.order_by('-updated_on').first()
    return render(request, 'views_pay_salary.html', {'cp': cp})


def payment_history(request):
    if not hasattr(request.user, 'employee_profile'):
        messages.error(request, "You must be logged in as an employee to view this page.")
        return redirect('home')
    employee = request.user.employee_profile
    payslips = Payslip.objects.filter(employee=employee).order_by('-generated_date')
    return render(request, 'payment_history.html', {'payslips': payslips})


def views_payslips(request, employee_id):
    pay = Payslip.objects.filter(employee_id=employee_id).order_by('-generated_date')
    return render(request, 'views_payslips.html', {'pay': pay})

