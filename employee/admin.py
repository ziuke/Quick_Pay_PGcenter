from django.contrib import admin

from employee.models import Employee, LeaveRequest, Attendance, PerformanceReview, LeaveLimit

# Register your models here.
admin.site.register(Employee)
admin.site.register(LeaveRequest)
admin.site.register(Attendance)
admin.site.register(PerformanceReview)
admin.site.register(LeaveLimit)
