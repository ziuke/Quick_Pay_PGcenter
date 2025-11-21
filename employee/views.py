from datetime import date, timedelta

from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect

from employee.forms import LeaveRequestForm, AddEmployeeForm, EditEmployeeForm, PerformanceReviewForm
from employee.models import LeaveRequest, Employee, PerformanceReview, LeaveLimit, Attendance
from payroll.models import Payslip
from user.models import User
from user.views import create_notification


# Create your views here.

def view_leaves(request, employee_id):
    leave = LeaveRequest.objects.filter(em_id=employee_id)
    return render(request, 'view_leaves.html', {'leave': leave})


"""def add_leave(request):
    if request.method == 'POST':
        form = LeaveRequestForm(request.POST)
        if form.is_valid():
            leave = form.save(commit=False)
            employee = get_object_or_404(Employee, user=request.user)
            leave.em = employee
            leave.save()
            return redirect('view_leaves', employee_id=employee.id)
    else:
        form = LeaveRequestForm()

    return render(request, 'add_leave.html', {'form': form})
"""


def add_leave(request):
    employee = get_object_or_404(Employee, user=request.user)

    if request.method == 'POST':
        form = LeaveRequestForm(request.POST)
        if form.is_valid():
            leave = form.save(commit=False)
            leave.em = employee
            leave.save()
            messages.success(request, "Leave request submitted. Waiting for HR approval.")
            return redirect('view_leaves', employee_id=employee.id)
    else:
        form = LeaveRequestForm()

    remaining = get_remaining_leaves(employee)

    return render(request, 'add_leave.html', {
        'form': form,
        'remaining': remaining,
        'current_year': date.today().year,
    })


def manage_leaves(request):
    status_filter = request.GET.get('status', 'pending')
    if status_filter == 'all':
        leaves = LeaveRequest.objects.select_related('em__user').order_by('-applied_on')
    else:
        leaves = LeaveRequest.objects.select_related('em__user').filter(status=status_filter).order_by('-applied_on')
    return render(request, 'manage_leaves.html', {
        'leaves': leaves,
        'status_filter': status_filter
    })


"""def view_leave(request, leave_id):
    leave = get_object_or_404(LeaveRequest, id=leave_id)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'approve':
            leave.status = 'approved'
            leave.save()
        elif action == 'reject':
            leave.status = 'rejected'
            leave.save()
            create_notification(
                user=leave.em.user,
                message=f"Your leave request has been {leave.status}."
            )
        return redirect('manage_leaves')

    return render(request, 'view_leave.html', {'leave': leave})
"""


def view_leave(request, leave_id):
    leave = get_object_or_404(LeaveRequest, id=leave_id)

    if request.method == 'POST':
        action = request.POST.get('action')

        # ---- APPROVE LEAVE ----
        if action == 'approve':
            leave.status = 'approved'
            leave.save()

            # Auto-create attendance entries for leave dates
            current_date = leave.start_date
            while current_date <= leave.end_date:
                Attendance.objects.update_or_create(
                    employee=leave.em,
                    date=current_date,
                    defaults={
                        'status': 'leave',
                        'leave': leave
                    }
                )
                current_date += timedelta(days=1)

            # Notify employee
            create_notification(
                user=leave.em.user,
                message=f"Your leave request from {leave.start_date} to {leave.end_date} has been approved."
            )

        # ---- REJECT LEAVE ----
        elif action == 'reject':
            leave.status = 'rejected'
            leave.save()

            create_notification(
                user=leave.em.user,
                message=f"Your leave request from {leave.start_date} to {leave.end_date} has been rejected."
            )

        return redirect('manage_leaves')

    return render(request, 'view_leave.html', {"leave": leave})


def add_employee(request):
    if request.method == 'POST':
        form = AddEmployeeForm(request.POST)
        if form.is_valid():
            employee = form.save(commit=False)
            employee.save()
            create_notification(
                user=employee.user,
                message=f"Your department has been assigned to {employee.department} department. "
            )
            messages.success(request, f"Employee profile created for {employee.user.username}")
            return redirect('h_home')
    else:
        form = AddEmployeeForm()

    return render(request, 'add_employee.html', {'form': form})


def edit_employee(request, employee_id):
    em = get_object_or_404(Employee, id=employee_id)
    if request.method == 'POST':
        form = EditEmployeeForm(request.POST, instance=em)
        if form.is_valid():
            form.save()
            create_notification(
                user=em.user,
                message=f"Your details were edited by the HR."
            )
            messages.success(request, "Employee details updated successfully!")
            return redirect('view_employees')
    else:
        form = EditEmployeeForm(instance=em)
    return render(request, 'edit_employee.html', {'form': form, 'employee': em})


def view_employees(request):
    employees = Employee.objects.select_related('user').all()
    print("Found employees:", employees.count())
    return render(request, 'view_employees.html', {'employees': employees})


def views_employees(request):
    employees = Employee.objects.select_related('user').all()
    return render(request, 'views_employees.html', {'employees': employees})


def add_performance_review(request, employee_id):
    if request.user.role != 'hr_manager':
        messages.error(request, "Access denied.")
        return redirect('home')
    employee = get_object_or_404(Employee, id=employee_id)
    if request.method == 'POST':
        form = PerformanceReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.employee = employee  # Associate the review with the employee
            review.reviewed_by = request.user
            review.save()
            messages.success(request, "Performance review added successfully!")
            return redirect('view_performance_review', employee_id=employee.id)
    else:
        form = PerformanceReviewForm()
    return render(request, 'add_performance_review.html', {'form': form, 'employee': employee})


def view_performance_review(request, employee_id):
    if request.user.role != 'hr_manager':
        messages.error(request, "Access denied.")
        return redirect('home')
    employee = get_object_or_404(Employee, id=employee_id)
    reviews = PerformanceReview.objects.filter(employee=employee)
    return render(request, 'view_performance_reviews.html', {
        'reviews': reviews,
        'employee': employee,
    })


def get_leave_usage(employee):
    current_year = date.today().year

    # Count all approved leaves (both sick + vacation)
    total_used = LeaveRequest.objects.filter(
        em=employee,
        status="approved",
        start_date__year=current_year
    ).count()

    return {
        "total_used": total_used
    }


def get_remaining_leaves(employee):
    TOTAL_LIMIT = 15  # yearly paid leave limit

    usage = get_leave_usage(employee)

    return {
        "remaining": TOTAL_LIMIT - usage["total_used"]
    }
