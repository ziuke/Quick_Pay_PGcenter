from django.conf import settings
from django.db import models
from django.utils import timezone

from user.models import User


# Create your models here.
class Employee(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('on_leave', 'On Leave'),
        ('terminated', 'Terminated'),
    ]

    DEPARTMENT_CHOICES = [
        ('hr', 'Human Resources'),
        ('finance', 'Finance'),
        ('it', 'Information Technology'),
        ('marketing', 'Marketing'),
        ('sales', 'Sales'),
        ('operations', 'Operations'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='employee_profile'
    )
    department = models.CharField(max_length=100, choices=DEPARTMENT_CHOICES, default='it')
    hire_date = models.DateField()
    salary = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    updated_on = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.pk and not self.hire_date:
            if self.user and self.user.date_joined:
                self.hire_date = self.user.date_joined.date()
            else:
                self.hire_date = timezone.now().date()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.get_department_display()}"


class LeaveRequest(models.Model):
    LEAVE_TYPES = [
        ('sick', 'Sick'),
        ('vacation', 'Vacation'),
    ]
    STATUS = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    em = models.ForeignKey(Employee, on_delete=models.CASCADE)
    type = models.CharField(max_length=20, choices=LEAVE_TYPES)
    status = models.CharField(max_length=20, choices=STATUS, default='pending')
    applied_on = models.DateTimeField(auto_now_add=True)
    start_date = models.DateField()
    end_date = models.DateField()
    is_unpaid = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.em.user.username} | {self.type} | {self.status}"


class LeaveLimit(models.Model):
    sick_limit = models.IntegerField(default=12)
    vacation_limit = models.IntegerField(default=12)

    def __str__(self):
        return "Global Leave Limits"


class Attendance(models.Model):
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('leave', 'Leave'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='present')
    leave = models.ForeignKey(LeaveRequest, null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        unique_together = ('employee', 'date')
        ordering = ['-date']

    def __str__(self):
        return f"{self.employee.user.username} - {self.date} ({self.status})"


BONUS_PERCENTAGE = {
    1: 0,
    2: 4,
    3: 8,
    4: 15,
    5: 25,
}


class PerformanceReview(models.Model):
    RATING_CHOICES = [
        (1, "Poor"),
        (2, "Average"),
        (3, "Good"),
        (4, "Very Good"),
        (5, "Excellent"),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="performance_reviews")
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, null=True, blank=True,
        limit_choices_to={'role': 'hr_manager'}
    )
    review_date = models.DateField(auto_now_add=True)
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES)
    comments = models.TextField(blank=True)
    increment_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    bonus_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        db_table = "performance_reviews"
        ordering = ['-review_date']

    def __str__(self):
        return f"{self.employee.user.username} - {self.get_rating_display()} ({self.review_date})"

    def save(self, *args, **kwargs):
        # Auto calculate bonus
        percent = BONUS_PERCENTAGE.get(self.rating, 0)
        basic_salary = self.employee.salary

        self.bonus_amount = (basic_salary * percent) / 100
        super().save(*args, **kwargs)
