from django.urls import path
import employee.views

urlpatterns = [
    path('view_leaves/<int:employee_id>/', employee.views.view_leaves, name='view_leaves'),
    path('add_leave', employee.views.add_leave, name='add_leave'),
    path('manage_leaves', employee.views.manage_leaves, name='manage_leaves'),
    path('view_leave/<int:employee_id>/', employee.views.view_leave, name='view_leave'),
    path('add_employee', employee.views.add_employee, name='add_employee'),
    path('edit_employee/<int:employee_id>/', employee.views.edit_employee, name='edit_employee'),
    path('view_employees/', employee.views.view_employees, name='view_employees'),
    path('views_employees/', employee.views.views_employees, name='views_employees'),
    path('add_performance_review', employee.views.add_performance_review, name='add_performance_review'),
    path('view_performance_reviews', employee.views.view_performance_reviews, name='view_performance_reviews'),
]