from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render

# Create your views here.
from django.shortcuts import render
from django.db.models import Sum, Count
from django.utils.timezone import now
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import TableStyle, Table, Spacer, Paragraph, SimpleDocTemplate

from payroll.models import Payroll, TotalDeductions
from datetime import datetime


@login_required()
def payroll_summary(request):
    month = int(request.GET.get('month', datetime.now().month))
    year = int(request.GET.get('year', datetime.now().year))
    payrolls = Payroll.objects.filter(
        payment_date__month=month,
        payment_date__year=year
    )
    totals = payrolls.aggregate(
        total_gross=Sum('gross__gross_total'),
        total_deductions=Sum('deductions__total_deduction'),
        total_net=Sum('net_salary')
    )
    context = {
        'payrolls': payrolls,
        'totals': totals,
        'month': month,
        'year': year,
    }
    return render(request, 'payroll_summary.html', context)


@login_required()
def generate_payroll_pdf(request):
    month = int(request.GET.get('month', datetime.now().month))
    year = int(request.GET.get('year', datetime.now().year))

    payrolls = Payroll.objects.filter(payment_date__month=month, payment_date__year=year)
    totals = payrolls.aggregate(
        total_gross=Sum('gross__gross_total'),
        total_deductions=Sum('deductions__total_deduction'),
        total_net=Sum('net_salary')
    )

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="payroll_summary_{month}_{year}.pdf"'

    doc = SimpleDocTemplate(response, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    title = Paragraph(f"<b>Payroll Summary Report - {month}/{year}</b>", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 12))

    data = [["Employee", "Gross Salary (Rs.)", "Total Deductions (Rs.)", "Net Salary (Rs.)"]]
    for p in payrolls:
        data.append([
            p.employee.user.username,
            f"{p.gross.gross_total:.2f}",
            f"{p.deductions.total_deduction:.2f}",
            f"{p.net_salary:.2f}",
        ])

    data.append([
        "TOTAL",
        f"{totals['total_gross'] or 0:.2f}",
        f"{totals['total_deductions'] or 0:.2f}",
        f"{totals['total_net'] or 0:.2f}"
    ])

    table = Table(data, colWidths=[2.5 * inch, 1.5 * inch, 1.5 * inch, 1.5 * inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#003366")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
    ]))

    elements.append(table)
    doc.build(elements)
    return response


@login_required()
def tax_deduction_report(request):
    month = int(request.GET.get('month', datetime.now().month))
    year = int(request.GET.get('year', datetime.now().year))

    # Filter deductions for selected month & year
    deductions = TotalDeductions.objects.filter(date__month=month, date__year=year)

    # Aggregate totals
    totals = deductions.aggregate(
        total_pf=Sum('pf'),
        total_esi=Sum('esi'),
        total_pt=Sum('pt'),
        total_income_tax=Sum('income_tax'),
        total_deduction=Sum('total_deduction'),
    )

    # Handle None safely
    for key in totals:
        totals[key] = totals[key] or 0

    context = {
        'deductions': deductions,
        'totals': totals,
        'month': month,
        'year': year,
    }

    return render(request, 'tax_deduction_report.html', context)


@login_required()
def tax_deduction_report_pdf(request):
    month = int(request.GET.get('month', datetime.now().month))
    year = int(request.GET.get('year', datetime.now().year))

    deductions = TotalDeductions.objects.filter(
        date__month=month,
        date__year=year
    ).select_related('employee')

    totals = deductions.aggregate(
        total_pf=Sum('pf'),
        total_esi=Sum('esi'),
        total_pt=Sum('pt'),
        total_income_tax=Sum('income_tax'),
        total_deduction=Sum('total_deduction')
    )

    # Create the response
    response = HttpResponse(content_type='application/pdf')
    filename = f"tax_deduction_report_{month}_{year}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    # Setup PDF
    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4
    y = height - 80

    # Header
    p.setFont("Helvetica-Bold", 16)
    p.drawCentredString(width / 2, y, f"Tax Deduction Report - {month}/{year}")
    y -= 40

    # Table Header
    p.setFont("Helvetica-Bold", 10)
    p.drawString(50, y, "Employee")
    p.drawString(180, y, "PF (Rs)")
    p.drawString(250, y, "ESI (Rs)")
    p.drawString(320, y, "PT (Rs)")
    p.drawString(390, y, "Income Tax (Rs)")
    p.drawString(490, y, "Total Deduction (Rs)")
    y -= 20
    p.setFont("Helvetica", 10)

    # Table Rows
    for d in deductions:
        if y < 80:
            p.showPage()
            y = height - 80
        p.drawString(50, y, str(d.employee.user.username))
        p.drawRightString(220, y, f"{d.pf:.2f}")
        p.drawRightString(290, y, f"{d.esi:.2f}")
        p.drawRightString(360, y, f"{d.pt:.2f}")
        p.drawRightString(460, y, f"{d.income_tax:.2f}")
        p.drawRightString(560, y, f"{d.total_deduction:.2f}")
        y -= 20

    # Totals
    y -= 20
    p.setFont("Helvetica-Bold", 10)
    p.drawString(50, y, "TOTAL")
    p.drawRightString(220, y, f"{totals['total_pf'] or 0:.2f}")
    p.drawRightString(290, y, f"{totals['total_esi'] or 0:.2f}")
    p.drawRightString(360, y, f"{totals['total_pt'] or 0:.2f}")
    p.drawRightString(460, y, f"{totals['total_income_tax'] or 0:.2f}")
    p.drawRightString(560, y, f"{totals['total_deduction'] or 0:.2f}")

    p.showPage()
    p.save()
    return response


User = get_user_model()


@login_required()
def admin_analytics(request):
    """Dashboard analytics for admin overview."""

    # Exclude admin/superuser
    users = User.objects.filter(is_superuser=False)

    total_users = users.count()
    active_users = users.filter(is_active=True).count()
    inactive_users = total_users - active_users

    # Users by role (excluding admin)
    users_by_role = (
        users.values('role')
        .annotate(count=Count('id'))
        .order_by('role')
    )

    from payroll.models import Payroll
    from user.models import Feedback

    total_payrolls = Payroll.objects.count()
    total_net_salary = Payroll.objects.aggregate(Sum('net_salary'))['net_salary__sum'] or 0

    # Feedback statistics
    reviewed_feedbacks = Feedback.objects.filter(status='Reviewed').count()
    pending_feedbacks = Feedback.objects.exclude(status='Reviewed').count()

    context = {
        'total_users': total_users,
        'active_users': active_users,
        'inactive_users': inactive_users,
        'users_by_role': users_by_role,
        'total_payrolls': total_payrolls,
        'total_net_salary': total_net_salary,
        'reviewed_feedbacks': reviewed_feedbacks,
        'pending_feedbacks': pending_feedbacks,
    }
    return render(request, 'admin_analytics.html', context)


@login_required()
def generate_admin_report_pdf(request):
    """Generate PDF for admin system analytics report."""
    from io import BytesIO
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []

    styles = getSampleStyleSheet()
    title = Paragraph("<b>QuickPay - Admin System Analytics Report</b>", styles["Title"])
    elements.append(title)
    elements.append(Spacer(1, 0.2 * inch))

    now_date = Paragraph(f"Generated on: {now().strftime('%d %B %Y, %I:%M %p')}", styles["Normal"])
    elements.append(now_date)
    elements.append(Spacer(1, 0.3 * inch))

    # System stats table
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    inactive_users = total_users - active_users
    total_payrolls = Payroll.objects.count()
    total_net_salary = Payroll.objects.aggregate(Sum('net_salary'))['net_salary__sum'] or 0

    data = [
        ["Metric", "Value"],
        ["Total Users", total_users],
        ["Active Users", active_users],
        ["Inactive Users", inactive_users],
        ["Total Payrolls Processed", total_payrolls],
        ["Total Net Salary Paid (Rs)", f"{total_net_salary:,.2f}"],
    ]

    table = Table(data, colWidths=[3 * inch, 3 * inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ]))
    elements.append(table)

    elements.append(Spacer(1, 0.4 * inch))

    # Save and return
    doc.build(elements)
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="Admin_Analytics_Report.pdf"'
    return response
