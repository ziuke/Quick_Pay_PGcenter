import random
import string
from datetime import date

from django.contrib import messages, auth
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail
from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login as auth_login, get_user_model
from django.utils import timezone
from django.views.decorators.http import require_POST

from employee.models import Employee
from user.forms import UserLoginForm, AddUserForm, UserProfileForm, FeedbackForm
from user.models import User, Notification, Feedback


# Create your views here.

def home(request):
    return render(request, 'home.html')


def login(request):
    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if not user.is_active:
                messages.error(request, "Your account has been blocked. Contact admin.")
                return redirect('login')
            auth_login(request, user)
            if user.is_superuser or user.role == "admin":
                return redirect('admin_home')
            elif user.role == "employee":
                return redirect('e_home')
            elif user.role == "hr_manager":
                return redirect('h_home')
            elif user.role == "payroll_manager":
                return redirect('pr_home')
            else:
                messages.error(request, "Unknown user role. Contact admin.")
                return redirect('login')
        else:
            messages.error(request, "Invalid username or password")
    else:
        form = UserLoginForm()
    return render(request, 'login.html', {'form': form})


def reset_password(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        phone = request.POST.get('phone')
        new_pw = request.POST.get('new_password')
        confirm_pw = request.POST.get('confirm_password')
        try:
            user = User.objects.get(username=username, phone=phone)
            if new_pw != confirm_pw:
                messages.error(request, "Passwords do not match.")
                return redirect('reset_password')
            user.set_password(new_pw)
            user.save()
            messages.success(request, "Password reset successful. Please login with your new password.")
            return redirect('login')
        except User.DoesNotExist:
            messages.error(request, "Invalid username or phone number.")
            return redirect('reset_password')
    return render(request, 'reset_password.html')


@login_required()
def admin_home(request):
    return render(request, 'admin_home.html')


@login_required()
def e_home(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:5]
    return render(request, 'e_home.html', {
        'notifications': notifications})


@login_required()
def h_home(request):
    return render(request, 'h_home.html')


@login_required()
def pr_home(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:5]
    return render(request, 'pr_home.html', {'notifications': notifications})


def about_us(request):
    return render(request, 'about_us.html')


def contact_us(request):
    return render(request, 'contact_us.html')


@login_required()
def logout(request):
    auth.logout(request)
    return redirect('home')


@login_required()
def manage_users(request):
    u = User.objects.exclude(role='admin').exclude(is_superuser=True)

    # Filtering logic
    role_filter = request.GET.get('role')
    status_filter = request.GET.get('status')

    if role_filter:
        u = u.filter(role=role_filter)
    if status_filter == 'active':
        u = u.filter(is_active=True)
    elif status_filter == 'blocked':
        u = u.filter(is_active=False)
    elif status_filter == 'approved':
        u = u.filter(is_approved=True)

    return render(request, 'manage_users.html', {
        'u': u,
        'role_filter': role_filter,
        'status_filter': status_filter
    })


@require_POST
def toggle_user_status(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.is_active = not user.is_active
    user.save()
    messages.success(request, f"{user.first_name} {user.last_name}'s account status updated.")
    return redirect('manage_users')


@require_POST
def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.delete()
    messages.success(request, f"User {user.first_name} deleted successfully.")
    return redirect('manage_users')


def generate_username(first_name):
    base = f"{first_name}".lower().replace(" ", "")
    suffix = random.randint(100, 999)
    return f"{base}{suffix}"


def generate_password():
    chars = string.ascii_letters + string.digits + "@$!#%"
    return ''.join(random.choice(chars) for _ in range(8))


@login_required()
def add_user(request):
    if request.method == 'POST':
        form = AddUserForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)

            # Auto-generate username & password
            user.username = generate_username(user.first_name)
            raw_password = generate_password()
            user.password = make_password(raw_password)

            # Generate office email
            domain = "quickpay.com"
            user.office_mail = f"{user.username}@{domain}"

            user.save()

            # Send email
            send_mail(
                subject="Welcome to QuickPay Payroll System",
                message=(
                    f"Dear {user.first_name} {user.last_name},\n\n"
                    f"Your QuickPay account has been created.\n"
                    f"Username: {user.username}\n"
                    f"Office Email: {user.office_mail}\n"
                    f"Password: {raw_password}\n\n"
                    f"Please log in and change your password.\n\n"
                    f"- QuickPay Admin"
                ),
                from_email="no-reply@quickpay.com",
                recipient_list=[user.email],
                fail_silently=True,
            )

            messages.success(request, "User added successfully and credentials emailed.")
            return redirect('admin_home')

        else:
            # ❌ Form Invalid → Show Toast Error
            messages.error(request, "Please correct the errors in the form and try again.")

    else:
        form = AddUserForm()

    return render(request, 'reg.html', {'form': form})


@login_required()
def edit_profile(request):
    if not request.user.is_authenticated:
        messages.error(request, "You must be logged in to edit your profile.")
        return redirect("login")

    user = request.user
    employee = getattr(user, "employee_profile", None)

    if request.method == "POST":
        form = UserProfileForm(request.POST, instance=user)
        if form.is_valid():
            # Save the user data
            old_password = user.password
            updated_user = form.save()

            if form.cleaned_data.get("password") and updated_user.password != old_password:
                logout(request)
                messages.success(request, "Password changed successfully. Please log in again.")
                return redirect("login")
            create_notification(
                user=user,
                message=f"Profile edited successfully"
            )
            messages.success(request, "Profile updated successfully.")

            # Redirect based on the user role
            if user.role == "admin":
                return redirect("admin_home")
            elif user.role == "hr_manager":
                return redirect("hr_home")
            elif user.role == "payroll_manager":
                return redirect("pr_home")
            elif user.role == "employee":
                return redirect("e_home")
            else:
                return redirect("home")
    else:
        form = UserProfileForm(instance=user)

    return render(request, "edit_profile.html", {
        "form": form,
        "employee": employee
    })


@login_required()
def submit_feedback(request):
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.user = request.user
            feedback.save()

            # Notifications
            create_notification(
                roles=['admin', 'hr_manager'],
                message=f"A feedback has been submitted by {request.user.username}."
            )
            create_notification(
                user=feedback.user,
                message="Your feedback has been submitted successfully."
            )

            # Show success message
            messages.success(request, "Your feedback has been submitted successfully.")
            return redirect('submit_feedback')  # redirect to the same form page
    else:
        form = FeedbackForm()

    return render(request, 'submit_feedback.html', {'form': form})


@login_required()
def feedback_list(request):
    if request.user.is_superuser or request.user.groups.filter(name__in=['Admin', 'HR Manager']).exists():
        feedbacks = Feedback.objects.all().order_by('-created_on')
    else:
        feedbacks = Feedback.objects.filter(user=request.user)
    return render(request, 'feedback_list.html', {'feedbacks': feedbacks})


@login_required()
def update_feedback_status(request, pk):
    if (
            request.user.is_superuser
            or request.user.groups.filter(name='HR Manager').exists()
    ):
        feedback = get_object_or_404(Feedback, pk=pk)
        feedback.status = 'Reviewed'
        feedback.save()

        create_notification(
            user=feedback.user,
            message=f"Your feedback titled '{feedback.title}' has been reviewed."
        )

        return redirect('feedback_list')
    else:
        return HttpResponseForbidden("You are not authorized to perform this action.")


def create_notification(user=None, role=None, roles=None, message=""):
    """
    Create notifications for:
    - a single user (user)
    - all users of a given role (role)
    - or multiple roles (roles: list or tuple)
    """
    if not message.strip():
        return

    from django.contrib.auth import get_user_model
    User = get_user_model()

    if user:
        Notification.objects.create(user=user, message=message)

    elif role:
        recipients = User.objects.filter(role=role, is_active=True)
        for recipient in recipients:
            Notification.objects.create(user=recipient, message=message)

    elif roles:
        recipients = User.objects.filter(role__in=roles, is_active=True)
        for recipient in recipients:
            Notification.objects.create(user=recipient, message=message)


@login_required()
def view_notifications(request):
    """Show only the notifications that belong to the logged-in user."""
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'notifications.html', {'notifications': notifications})


def faq(request):
    return render(request, 'faq.html')
