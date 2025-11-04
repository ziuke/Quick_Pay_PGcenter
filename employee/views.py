from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect

from employee.forms import LeaveRequestForm, AddEmployeeForm, EditEmployeeForm, PerformanceReviewForm
from employee.models import LeaveRequest, Employee, PerformanceReview
from payroll.models import Payslip
from user.models import User
from user.views import create_notification


# Create your views here.

def view_leaves(request, employee_id):
    leave = LeaveRequest.objects.filter(em_id=employee_id)
    return render(request, 'view_leaves.html', {'leave': leave})


def add_leave(request):
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


def manage_leaves(request):
    # Get distinct employees who applied for leave
    leaves = LeaveRequest.objects.select_related('em__user').order_by('em__user__first_name')
    return render(request, 'manage_leaves.html', {'leaves': leaves})


def view_leave(request, employee_id):
    leave = get_object_or_404(LeaveRequest, em__id=employee_id)

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


def add_employee(request):
    if request.method == 'POST':
        form = AddEmployeeForm(request.POST)
        if form.is_valid():
            employee = form.save(commit=False)
            employee.save()
            create_notification(
                user=employee.user.username,
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


def add_performance_review(request):
    if request.user.role != 'hr_manager':
        messages.error(request, "Access denied.")
        return redirect('home')

    if request.method == 'POST':
        form = PerformanceReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.reviewed_by = request.user
            review.save()
            messages.success(request, "Performance review added successfully!")
            return redirect('view_performance_reviews')
    else:
        form = PerformanceReviewForm()
    return render(request, 'add_performance_review.html', {'form': form})


def view_performance_reviews(request):
    if request.user.role != 'hr_manager':
        messages.error(request, "Access denied.")
        return redirect('home')

    reviews = PerformanceReview.objects.select_related('employee').all()
    return render(request, 'view_performance_reviews.html', {'reviews': reviews})



