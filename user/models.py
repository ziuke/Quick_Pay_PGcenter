from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models

import employee


# Create your models here.

class User(AbstractUser):
    USER_TYPES = [
        ('admin', 'Admin'),
        ('hr_manager', 'HR Manager'),
        ('payroll_manager', 'Payroll Manager'),
        ('employee', 'Employee'),
    ]
    role = models.CharField(max_length=25, choices=USER_TYPES, default='employee')
    address = models.CharField(max_length=150, null=True, blank=True)
    phone = models.CharField(max_length=10, null=True, blank=True)
    office_mail = models.EmailField(unique=True, null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.is_superuser:
            self.role = 'admin'
            self.office_mail = self.email
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.username} ({self.role})"


class Notification(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications"
    )
    message = models.TextField(null=False, blank=False)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        db_table = "notifications"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Notification #{self.id} → {self.user.username}"


class Feedback(models.Model):
    STATUS_TYPES = [
        ('Pending', 'Pending'),
        ('Resolved', 'Resolved'),
        ('Reviewed', 'Reviewed'),
    ]
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="feedback"
    )
    created_on = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_TYPES, default='Pending')
    subject = models.CharField(max_length=250, null=True, blank=True)
    message = models.TextField()

    def __str__(self):
        return f"{self.user.username} - {self.subject}"





