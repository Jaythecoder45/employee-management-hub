from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('employee/<int:pk>/', views.employee_detail, name='employee_detail'),
    path('employee/add/', views.employee_create, name='employee_create'),
    path('employee/<int:pk>/edit/', views.employee_update, name='employee_update'),
    path('employee/<int:pk>/delete/', views.employee_delete, name='employee_delete'),
    path('export/csv/', views.export_employees_csv, name='export_employees_csv'),
    path('employee/<int:pk>/pdf/', views.generate_employee_pdf, name='generate_employee_pdf'),
    path('import/csv/', views.import_employees_csv, name='import_employees_csv'),
    path('departments/<str:dept_name>/', views.department_view, name='department_view'),
    path('employee/<int:pk>/task/assign/', views.assign_task, name='assign_task'),
    path('task/<int:task_id>/evaluate/', views.evaluate_task, name='evaluate_task'),
    path('portal/', views.portal_view, name='employee_portal'),
    path('tasks/bulk-assign/', views.bulk_assign_task, name='bulk_assign_task'),
    path('task/<int:task_id>/status/', views.update_task_status, name='update_task_status'),
    path('task/<int:task_id>/submit/', views.submit_task_work, name='submit_task_work'),
    path('notifications/mark-read/', views.mark_notifications_read, name='mark_notifications_read'),
    path('portal/password-change/', views.EmployeePasswordChangeView.as_view(), name='password_change'),
    path('login/', auth_views.LoginView.as_view(template_name='employees/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]
