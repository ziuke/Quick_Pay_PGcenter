from django.urls import path
import user.views

urlpatterns = [
    path('', user.views.home, name='home1'),
    path('home', user.views.home, name='home'),
    path('add_user', user.views.add_user, name='add_user'),
    path('login', user.views.login, name='login'),
    path('reset_password', user.views.reset_password, name='reset_password'),
    path('admin_home', user.views.admin_home, name='admin_home'),
    path('e_home', user.views.e_home, name='e_home'),
    path('pr_home', user.views.pr_home, name='pr_home'),
    path('h_home', user.views.h_home, name='h_home'),
    path('about_us', user.views.about_us, name='about_us'),
    path('contact_us', user.views.contact_us, name='contact_us'),
    path('logout', user.views.logout, name='logout'),
    path('manage_users', user.views.manage_users, name='manage_users'),
    path('toggle_user_status/<int:user_id>/', user.views.toggle_user_status, name='toggle_user_status'),
    path('delete_user/<int:user_id>/', user.views.delete_user, name='delete_user'),
    path('generate_username', user.views.generate_username, name='generate_username'),
    path('generate_password', user.views.generate_password, name='generate_password'),
    path('edit_profile', user.views.edit_profile, name='edit_profile'),
    path('submit_feedback', user.views.submit_feedback, name='submit_feedback'),
    path('feedback_list', user.views.feedback_list, name='feedback_list'),
    path('update_feedback_status/<int:pk>/', user.views.update_feedback_status, name='update_feedback_status'),
    path('view_notifications', user.views.view_notifications, name='view_notifications'),
]
