from django.contrib import admin

from employee.models import Employee, LeaveRequest

# Register your models here.
admin.site.register(Employee)
admin.site.register(LeaveRequest)
