from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from datetime import date
from .models import Employee
from .forms import EmployeeForm

class EmployeeModelTests(TestCase):
    def test_employee_id_auto_generation(self):
        # Create an employee
        emp1 = Employee.objects.create(
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            phone="1234567890",
            job_title="Software Engineer",
            department="Engineering",
            salary=75000.00,
            hire_date=date(2026, 1, 1),
            status="Active"
        )
        self.assertEqual(emp1.employee_id, "EMP-1001")
        
        # Create another employee to check sequential increments
        emp2 = Employee.objects.create(
            first_name="Jane",
            last_name="Smith",
            email="jane.smith@example.com",
            phone="0987654321",
            job_title="Designer",
            department="Marketing",
            salary=68000.00,
            hire_date=date(2026, 2, 1),
            status="Active"
        )
        self.assertEqual(emp2.employee_id, "EMP-1002")

class EmployeeViewsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='admin', password='password123')
        self.user.is_staff = True
        self.user.is_superuser = True
        self.user.save()
        self.client.login(username='admin', password='password123')
        
        self.employee = Employee.objects.create(
            first_name="Alice",
            last_name="Johnson",
            email="alice.johnson@example.com",
            phone="5551234567",
            job_title="Project Manager",
            department="Operations",
            salary=85000.00,
            hire_date=date(2026, 3, 1),
            status="Active",
            notes="Experienced Scrum Master."
        )

    def test_unauthenticated_redirect(self):
        self.client.logout()
        response = self.client.get(reverse('dashboard'))
        self.assertRedirects(response, f"/login/?next={reverse('dashboard')}")

    def test_dashboard_view(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Alice Johnson")
        self.assertContains(response, "EMP-1001")

    def test_employee_detail_view(self):
        response = self.client.get(reverse('employee_detail', kwargs={'pk': self.employee.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Alice Johnson")
        self.assertContains(response, "Experienced Scrum Master")

    def test_employee_create_view_get(self):
        response = self.client.get(reverse('employee_create'))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context['form'], EmployeeForm)

    def test_employee_create_view_post_success(self):
        data = {
            'first_name': 'Bob',
            'last_name': 'Miller',
            'email': 'bob.miller@example.com',
            'phone': '5559876543',
            'job_title': 'Accountant',
            'department': 'Finance',
            'salary': 62000.00,
            'hire_date': '2026-04-15',
            'status': 'Active',
            'notes': 'New finance team member.'
        }
        response = self.client.post(reverse('employee_create'), data=data)
        new_emp = Employee.objects.get(email='bob.miller@example.com')
        self.assertRedirects(response, reverse('employee_detail', kwargs={'pk': new_emp.pk}))
        self.assertEqual(new_emp.employee_id, 'EMP-1002')

    def test_employee_update_view_post(self):
        data = {
            'first_name': 'Alice',
            'last_name': 'Johnson',
            'email': 'alice.new@example.com', # Updated
            'phone': '5551234567',
            'job_title': 'Senior Project Manager', # Updated
            'department': 'Operations',
            'salary': 90000.00, # Updated
            'hire_date': '2026-03-01',
            'status': 'Active',
            'notes': 'Promoted Scrum Master.'
        }
        response = self.client.post(reverse('employee_update', kwargs={'pk': self.employee.pk}), data=data)
        self.employee.refresh_from_db()
        self.assertEqual(self.employee.email, 'alice.new@example.com')
        self.assertEqual(self.employee.job_title, 'Senior Project Manager')
        self.assertEqual(self.employee.salary, 90000.00)
        self.assertRedirects(response, reverse('employee_detail', kwargs={'pk': self.employee.pk}))

    def test_employee_delete_view_post(self):
        # Verify it exists
        self.assertTrue(Employee.objects.filter(pk=self.employee.pk).exists())
        
        # Post to delete
        response = self.client.post(reverse('employee_delete', kwargs={'pk': self.employee.pk}))
        self.assertRedirects(response, reverse('dashboard'))
        self.assertFalse(Employee.objects.filter(pk=self.employee.pk).exists())

    def test_dashboard_salary_range_filter(self):
        # Create another employee with different salary
        Employee.objects.create(
            first_name="Rich",
            last_name="Guy",
            email="rich.guy@example.com",
            phone="1112223333",
            job_title="VP Engineering",
            department="Engineering",
            salary=150000.00,
            hire_date=date(2026, 1, 1),
            status="Active"
        )
        # Verify with min salary filter
        response = self.client.get(reverse('dashboard') + '?min_salary=100000')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Rich Guy")
        self.assertNotContains(response, "Alice Johnson") # Alice makes 85k

        # Verify with max salary filter
        response2 = self.client.get(reverse('dashboard') + '?max_salary=90000')
        self.assertEqual(response2.status_code, 200)
        self.assertContains(response2, "Alice Johnson")
        self.assertNotContains(response2, "Rich Guy")

    def test_export_csv(self):
        response = self.client.get(reverse('export_employees_csv'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertTrue(response['Content-Disposition'].startswith('attachment; filename="employees_export.csv"'))
        
        content = response.content.decode('utf-8')
        self.assertIn("Alice,Johnson,alice.johnson@example.com", content)
        self.assertIn("Employee ID,First Name,Last Name", content)

    def test_generate_pdf(self):
        from .models import ActivityLog
        response = self.client.get(reverse('generate_employee_pdf', kwargs={'pk': self.employee.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        # Check ActivityLog
        self.assertTrue(ActivityLog.objects.filter(action_type='Update').exists())

    def test_import_employees_csv_success(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        from .models import ActivityLog
        
        csv_content = (
            "First Name,Last Name,Email,Phone,Job Title,Department,Salary,Hire Date,Status\n"
            "Bob,Smith,bob.smith@example.com,555-9876,Developer,Engineering,75000.00,2026-06-01,Active\n"
        )
        csv_file = SimpleUploadedFile("employees.csv", csv_content.encode('utf-8'), content_type="text/csv")
        
        initial_count = Employee.objects.count()
        response = self.client.post(reverse('import_employees_csv'), {'csv_file': csv_file})
        self.assertRedirects(response, reverse('dashboard'))
        self.assertEqual(Employee.objects.count(), initial_count + 1)
        
        bob = Employee.objects.get(email='bob.smith@example.com')
        self.assertEqual(bob.first_name, 'Bob')
        self.assertEqual(bob.salary, 75000.00)
        
        # Check ActivityLog
        self.assertTrue(ActivityLog.objects.filter(action_type='Import').exists())

    def test_assign_task_view(self):
        from .models import EmployeeTask
        response = self.client.post(reverse('assign_task', kwargs={'pk': self.employee.pk}), {
            'title': 'Test Task',
            'description': 'Description details',
            'due_date': '2026-08-01',
            'status': 'Pending'
        })
        self.assertRedirects(response, reverse('employee_detail', kwargs={'pk': self.employee.pk}))
        self.assertEqual(EmployeeTask.objects.filter(employee=self.employee).count(), 1)
        task = EmployeeTask.objects.get(employee=self.employee)
        self.assertEqual(task.title, 'Test Task')

    def test_evaluate_task_view(self):
        from .models import EmployeeTask
        task = EmployeeTask.objects.create(
            employee=self.employee,
            title='Evaluate Me',
            due_date=date(2026, 8, 1),
            status='Pending'
        )
        response = self.client.post(reverse('evaluate_task', kwargs={'task_id': task.pk}), {
            'status': 'Completed',
            'rating': 5,
            'grade': 'A+',
            'feedback': 'Terrific effort!'
        })
        self.assertRedirects(response, reverse('employee_detail', kwargs={'pk': self.employee.pk}))
        task.refresh_from_db()
        self.assertEqual(task.status, 'Completed')
        self.assertEqual(task.rating, 5)
        self.assertEqual(task.grade, 'A+')

    def test_department_view_filtering(self):
        Employee.objects.create(
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            phone="9998887777",
            job_title="Sales Rep",
            department="Sales",
            salary=50000.00,
            hire_date=date(2026, 4, 1),
            status="Active"
        )
        response = self.client.get(reverse('department_view', kwargs={'dept_name': 'Operations'}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Alice Johnson")
        self.assertNotContains(response, "John Doe")

        response2 = self.client.get(reverse('department_view', kwargs={'dept_name': 'Sales'}))
        self.assertEqual(response2.status_code, 200)
        self.assertContains(response2, "John Doe")
        self.assertNotContains(response2, "Alice Johnson")

    def test_role_based_redirection_and_access(self):
        from django.contrib.auth.models import User
        emp_user = User.objects.create_user(username='elena@example.com', email='elena@example.com', password='welcome123')
        self.employee.user = emp_user
        self.employee.email = 'elena@example.com'
        self.employee.save()
        
        self.client.login(username='elena@example.com', password='welcome123')
        response = self.client.get(reverse('dashboard'))
        self.assertRedirects(response, reverse('employee_portal'))
        
        response = self.client.get(reverse('employee_portal'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Alice Johnson")
        
        response = self.client.get(reverse('department_view', kwargs={'dept_name': 'Operations'}))
        self.assertEqual(response.status_code, 403)
        
        response = self.client.get(reverse('bulk_assign_task'))
        self.assertEqual(response.status_code, 403)

    def test_bulk_task_assignment_view(self):
        from .models import EmployeeTask, Employee
        emp2 = Employee.objects.create(
            first_name="Elena",
            last_name="Smith",
            email="elena@example.com",
            phone="111-2222",
            job_title="Designer",
            department="Marketing",
            salary=60000.00,
            hire_date=date(2026, 5, 1),
            status="Active"
        )
        self.client.login(username='admin', password='password123')
        response = self.client.post(reverse('bulk_assign_task'), {
            'title': 'Bulk Mission',
            'description': 'Description text',
            'due_date': '2026-09-01',
            'employees': [self.employee.pk, emp2.pk]
        })
        self.assertRedirects(response, reverse('dashboard'))
        self.assertEqual(EmployeeTask.objects.filter(title='Bulk Mission').count(), 2)

    def test_notification_creation_and_read_status(self):
        from .models import Notification, EmployeeTask
        task = EmployeeTask.objects.create(
            employee=self.employee,
            title='Update Me',
            due_date=date(2026, 8, 1),
            status='Pending'
        )
        
        from django.contrib.auth.models import User
        emp_user = User.objects.create_user(username='elena@example.com', email='elena@example.com', password='welcome123')
        self.employee.user = emp_user
        self.employee.email = 'elena@example.com'
        self.employee.save()
        
        self.client.login(username='elena@example.com', password='welcome123')
        from django.core.files.uploadedfile import SimpleUploadedFile
        test_file = SimpleUploadedFile("work.pdf", b"test content", content_type="application/pdf")
        response = self.client.post(reverse('submit_task_work', kwargs={'task_id': task.pk}), {
            'work_submission': test_file,
            'submission_notes': 'Task completed!'
        })
        self.assertRedirects(response, reverse('employee_portal'))
        
        task.refresh_from_db()
        self.assertEqual(task.status, 'Pending Review')
        self.assertTrue('work' in task.work_submission.name and task.work_submission.name.endswith('.pdf'))
        
        self.assertTrue(Notification.objects.filter(recipient=self.user, is_read=False).exists())
        
        self.client.login(username='admin', password='password123')
        response = self.client.get(reverse('mark_notifications_read'))
        self.assertFalse(Notification.objects.filter(recipient=self.user, is_read=False).exists())

    def test_password_change_view(self):
        from django.contrib.auth.models import User
        emp_user = User.objects.create_user(username='elena@example.com', email='elena@example.com', password='welcome123')
        self.employee.user = emp_user
        self.employee.email = 'elena@example.com'
        self.employee.save()
        
        self.client.login(username='elena@example.com', password='welcome123')
        response = self.client.get(reverse('password_change'))
        self.assertEqual(response.status_code, 200)
        
        response = self.client.post(reverse('password_change'), {
            'old_password': 'welcome123',
            'new_password1': 'securepass456',
            'new_password2': 'securepass456'
        })
        self.assertRedirects(response, reverse('employee_portal'))
        
        self.client.logout()
        logged_in = self.client.login(username='elena@example.com', password='securepass456')
        self.assertTrue(logged_in)

    def test_employee_cannot_mark_completed_directly(self):
        from django.contrib.auth.models import User
        from .models import EmployeeTask
        task = EmployeeTask.objects.create(
            employee=self.employee,
            title='Do Not Direct Complete',
            due_date=date(2026, 8, 1),
            status='Pending'
        )
        emp_user = User.objects.create_user(username='elena@example.com', password='welcome123')
        self.employee.user = emp_user
        self.employee.email = 'elena@example.com'
        self.employee.save()
        
        self.client.login(username='elena@example.com', password='welcome123')
        response = self.client.post(reverse('update_task_status', kwargs={'task_id': task.pk}), {
            'status': 'Completed'
        })
        self.assertRedirects(response, reverse('employee_portal'))
        task.refresh_from_db()
        self.assertEqual(task.status, 'Pending')

    def test_employee_email_change_sync(self):
        from django.contrib.auth.models import User
        emp_user = User.objects.create_user(username='elena@example.com', email='elena@example.com', password='welcome123')
        self.employee.user = emp_user
        self.employee.email = 'elena@example.com'
        self.employee.save()
        
        response = self.client.post(reverse('employee_update', kwargs={'pk': self.employee.pk}), {
            'first_name': self.employee.first_name,
            'last_name': self.employee.last_name,
            'email': 'new_elena@example.com',
            'phone': self.employee.phone,
            'job_title': self.employee.job_title,
            'department': self.employee.department,
            'salary': self.employee.salary,
            'hire_date': self.employee.hire_date.strftime('%Y-%m-%d'),
            'status': self.employee.status
        })
        self.assertRedirects(response, reverse('employee_detail', kwargs={'pk': self.employee.pk}))
        
        emp_user.refresh_from_db()
        self.assertEqual(emp_user.username, 'new_elena@example.com')
        self.assertEqual(emp_user.email, 'new_elena@example.com')
