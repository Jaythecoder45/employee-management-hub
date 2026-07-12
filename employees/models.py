import random
from django.db import models
from django.contrib.auth.models import User

class Employee(models.Model):
    DEPARTMENT_CHOICES = [
        ('Engineering', 'Engineering'),
        ('Sales', 'Sales'),
        ('HR', 'Human Resources'),
        ('Marketing', 'Marketing'),
        ('Finance', 'Finance'),
        ('Operations', 'Operations'),
    ]
    
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
        ('On Leave', 'On Leave'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='employee_profile')
    employee_id = models.CharField(max_length=15, unique=True, editable=False)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    job_title = models.CharField(max_length=100)
    department = models.CharField(max_length=50, choices=DEPARTMENT_CHOICES, default='Engineering')
    salary = models.DecimalField(max_digits=10, decimal_places=2)
    hire_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active')
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.employee_id:
            # Generate ID, e.g. EMP-1001
            last_emp = Employee.objects.all().order_by('id').last()
            if not last_emp:
                self.employee_id = 'EMP-1001'
            else:
                try:
                    last_id = int(last_emp.employee_id.split('-')[1])
                    self.employee_id = f'EMP-{last_id + 1}'
                except (IndexError, ValueError):
                    # Fallback in case of custom format
                    self.employee_id = f'EMP-{random.randint(1000, 9999)}'
        super().save(*args, **kwargs)
        
        # Synchronize linked User credentials if email changed
        if self.user:
            user_changed = False
            if self.user.username != self.email:
                self.user.username = self.email
                user_changed = True
            if self.user.email != self.email:
                self.user.email = self.email
                user_changed = True
            if user_changed:
                self.user.save()
        
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.employee_id})"



class ActivityLog(models.Model):
    ACTION_CHOICES = [
        ('Create', 'Create'),
        ('Update', 'Update'),
        ('Delete', 'Delete'),
        ('Import', 'Import'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action_type = models.CharField(max_length=20, choices=ACTION_CHOICES)
    description = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        
    def __str__(self):
        user_str = self.user.username if self.user else "System"
        return f"{user_str} - {self.action_type} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"

class EmployeeTask(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Pending Review', 'Pending Review'),
        ('Completed', 'Completed'),
        ('Failed', 'Failed'),
    ]
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    due_date = models.DateField()
    rating = models.IntegerField(blank=True, null=True) # 1-5 Stars
    grade = models.CharField(max_length=5, blank=True, null=True) # A+, A, B, C etc.
    feedback = models.TextField(blank=True, null=True)
    work_submission = models.FileField(upload_to='submissions/', null=True, blank=True)
    submission_notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['due_date', '-created_at']
        
    def __str__(self):
        return f"{self.title} - {self.employee.first_name} ({self.status})"

class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"Notification for {self.recipient.username}: {self.message[:30]}..."
