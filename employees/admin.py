from django.contrib import admin
from .models import Employee, ActivityLog, EmployeeTask, Notification

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('employee_id', 'first_name', 'last_name', 'email', 'job_title', 'department', 'status', 'hire_date')
    list_filter = ('department', 'status', 'hire_date')
    search_fields = ('employee_id', 'first_name', 'last_name', 'email', 'job_title')
    ordering = ('employee_id',)
    readonly_fields = ('employee_id', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Employee ID & Personal Info', {
            'fields': ('employee_id', 'first_name', 'last_name', 'email', 'phone')
        }),
        ('Job & Compensation Details', {
            'fields': ('job_title', 'department', 'salary', 'hire_date', 'status')
        }),
        ('Additional Info', {
            'fields': ('notes', 'created_at', 'updated_at')
        }),
    )

@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action_type', 'description', 'timestamp')
    list_filter = ('action_type', 'timestamp')
    search_fields = ('description', 'user__username')
    ordering = ('-timestamp',)
    readonly_fields = ('timestamp',)

@admin.register(EmployeeTask)
class EmployeeTaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'employee', 'status', 'due_date', 'rating', 'grade')
    list_filter = ('status', 'due_date', 'grade')
    search_fields = ('title', 'employee__first_name', 'employee__last_name', 'feedback')
    ordering = ('due_date',)

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'message', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('message', 'recipient__username')
    ordering = ('-created_at',)
