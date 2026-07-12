import csv
import json
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q, Avg, Count
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.views import PasswordChangeView
from django.contrib.messages.views import SuccessMessageMixin
from django.core.mail import send_mail
from django.conf import settings
from django.core.paginator import Paginator
from .models import Employee, ActivityLog, EmployeeTask, Notification
from .forms import EmployeeForm, EmployeeTaskForm, EmployeeTaskEvaluationForm, BulkTaskAssignmentForm, EmployeeTaskSubmissionForm

def send_employee_welcome_email(employee, request=None):
    host = request.get_host() if request else "127.0.0.1:8000"
    subject = "Welcome to Employee Hub | Your Portal Details"
    message = (
        f"Hi {employee.first_name},\n\n"
        f"An administrator has registered your profile in Employee Hub.\n"
        f"You can log in to your personal Employee Portal to track your tasks and submit updates.\n\n"
        f"Login Portal: http://{host}/login/\n"
        f"Username: {employee.email}\n"
        f"Password: welcome123\n\n"
        f"Please update your password after signing in.\n\n"
        f"Regards,\n"
        f"HR Operations Team"
    )
    try:
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None) or 'notifications@employeehub.com'
        send_mail(
            subject,
            message,
            from_email,
            [employee.email],
            fail_silently=True,
        )
    except Exception as e:
        print(f"Error sending welcome email: {e}")

def create_employee_user_account(employee, request=None):
    if not employee.user:
        username = employee.email
        if not User.objects.filter(username=username).exists():
            user = User.objects.create_user(username=username, email=employee.email, password='welcome123')
            user.first_name = employee.first_name
            user.last_name = employee.last_name
            user.save()
            employee.user = user
            employee.save()
            
            # Trigger welcome email dispatch log
            send_employee_welcome_email(employee, request)
            
            print(f"\n==================================================")
            print(f"AUTOMATED USER ACCOUNT CREATED:")
            print(f"  Employee: {employee.first_name} {employee.last_name}")
            print(f"  Username: {employee.email}")
            print(f"  Password: welcome123")
            print(f"==================================================\n")

@login_required
def dashboard(request):
    if not (request.user.is_superuser or request.user.is_staff):
        return redirect('employee_portal')
    # Base queryset
    employees = Employee.objects.all().order_by('-created_at')
    
    # Filtering parameters
    search_query = request.GET.get('search', '').strip()
    dept_filter = request.GET.get('department', '').strip()
    status_filter = request.GET.get('status', '').strip()
    min_salary = request.GET.get('min_salary', '').strip()
    max_salary = request.GET.get('max_salary', '').strip()
    sort_by = request.GET.get('sort', '').strip()
    
    if search_query:
        employees = employees.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(employee_id__icontains=search_query) |
            Q(job_title__icontains=search_query)
        )
        
    if dept_filter:
        employees = employees.filter(department=dept_filter)
        
    if status_filter:
        employees = employees.filter(status=status_filter)
        
    if min_salary:
        try:
            employees = employees.filter(salary__gte=float(min_salary))
        except (ValueError, TypeError):
            min_salary = ''
            
    if max_salary:
        try:
            employees = employees.filter(salary__lte=float(max_salary))
        except (ValueError, TypeError):
            max_salary = ''
        
    if sort_by:
        if sort_by == 'salary_asc':
            employees = employees.order_by('salary')
        elif sort_by == 'salary_desc':
            employees = employees.order_by('-salary')
        elif sort_by == 'hire_date_asc':
            employees = employees.order_by('hire_date')
        elif sort_by == 'hire_date_desc':
            employees = employees.order_by('-hire_date')
        elif sort_by == 'name_asc':
            employees = employees.order_by('first_name', 'last_name')
        elif sort_by == 'name_desc':
            employees = employees.order_by('-first_name', '-last_name')

    # Aggregations for dashboard cards
    total_count = Employee.objects.count()
    active_count = Employee.objects.filter(status='Active').count()
    on_leave_count = Employee.objects.filter(status='On Leave').count()
    avg_salary = Employee.objects.aggregate(Avg('salary'))['salary__avg'] or 0
    
    # Department counts for rendering a visual distribution
    dept_counts = Employee.objects.values('department').annotate(count=Count('id')).order_by('-count')
    max_dept_count = max([d['count'] for d in dept_counts]) if dept_counts else 0
    
    # Dynamic analytical charts inputs
    dept_labels = [item['department'] for item in dept_counts]
    dept_values = [item['count'] for item in dept_counts]
    
    salary_by_dept = Employee.objects.values('department').annotate(avg_salary=Avg('salary')).order_by('-avg_salary')
    salary_labels = [item['department'] for item in salary_by_dept]
    salary_values = [float(item['avg_salary']) for item in salary_by_dept]
    
    # Pagination - 8 items per page
    paginator = Paginator(employees, 8)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'employees': page_obj,
        'total_count': total_count,
        'active_count': active_count,
        'on_leave_count': on_leave_count,
        'avg_salary': avg_salary,
        'dept_counts': dept_counts,
        'max_dept_count': max_dept_count,
        'dept_labels_json': json.dumps(dept_labels),
        'dept_values_json': json.dumps(dept_values),
        'salary_labels_json': json.dumps(salary_labels),
        'salary_values_json': json.dumps(salary_values),
        'activity_logs': ActivityLog.objects.all().order_by('-timestamp')[:5],
        'search_query': search_query,
        'dept_filter': dept_filter,
        'status_filter': status_filter,
        'min_salary': min_salary,
        'max_salary': max_salary,
        'sort_by': sort_by,
        'departments': Employee.DEPARTMENT_CHOICES,
        'statuses': Employee.STATUS_CHOICES,
    }
    return render(request, 'employees/dashboard.html', context)

@login_required
def employee_detail(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    tasks = employee.tasks.all()
    total_tasks = tasks.count()
    completed_tasks = tasks.filter(status='Completed').count()
    completion_rate = int((completed_tasks / total_tasks * 100)) if total_tasks > 0 else 0
    avg_rating = tasks.filter(status='Completed', rating__isnull=False).aggregate(Avg('rating'))['rating__avg'] or 0
    
    context = {
        'employee': employee,
        'tasks': tasks,
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'completion_rate': completion_rate,
        'avg_rating': round(float(avg_rating), 1),
        'stars_range': range(1, 6),
    }
    return render(request, 'employees/employee_detail.html', context)

@login_required
def employee_create(request):
    if not (request.user.is_superuser or request.user.is_staff):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("Access Denied: Administrators only.")
        
    if request.method == 'POST':
        form = EmployeeForm(request.POST)
        if form.is_valid():
            employee = form.save()
            
            # Auto-create User account & link it
            try:
                create_employee_user_account(employee, request)
            except Exception as e:
                print(f"Error creating user account: {e}")
            
            # Create ActivityLog
            ActivityLog.objects.create(
                user=request.user,
                action_type='Create',
                description=f"Added new employee: {employee.first_name} {employee.last_name} ({employee.employee_id})."
            )
            messages.success(request, f"Employee {employee.first_name} {employee.last_name} created successfully!")
            return redirect('employee_detail', pk=employee.pk)
    else:
        dept_param = request.GET.get('department', '')
        if dept_param:
            form = EmployeeForm(initial={'department': dept_param})
        else:
            form = EmployeeForm()
    return render(request, 'employees/employee_form.html', {'form': form, 'title': 'Add New Employee'})

@login_required
def employee_update(request, pk):
    if not (request.user.is_superuser or request.user.is_staff):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("Access Denied: Administrators only.")
        
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        form = EmployeeForm(request.POST, instance=employee)
        if form.is_valid():
            employee = form.save()
            if hasattr(employee, 'user') and employee.user:
                employee.user.username = employee.email
                employee.user.email = employee.email
                employee.user.save()
            # Create ActivityLog
            ActivityLog.objects.create(
                user=request.user,
                action_type='Update',
                description=f"Updated details for employee: {employee.first_name} {employee.last_name} ({employee.employee_id})."
            )
            messages.success(request, f"Employee {employee.first_name} {employee.last_name} updated successfully!")
            return redirect('employee_detail', pk=employee.pk)
    else:
        form = EmployeeForm(instance=employee)
    return render(request, 'employees/employee_form.html', {'form': form, 'employee': employee, 'title': 'Edit Employee Details'})

@login_required
def employee_delete(request, pk):
    if not (request.user.is_superuser or request.user.is_staff):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("Access Denied: Administrators only.")
        
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        name = f"{employee.first_name} {employee.last_name}"
        emp_id = employee.employee_id
        employee.delete()
        # Create ActivityLog
        ActivityLog.objects.create(
            user=request.user,
            action_type='Delete',
            description=f"Deleted employee record for: {name} ({emp_id})."
        )
        messages.success(request, f"Employee {name} was successfully deleted.")
        return redirect('dashboard')
    return render(request, 'employees/employee_confirm_delete.html', {'employee': employee})

@login_required
def export_employees_csv(request):
    if not (request.user.is_superuser or request.user.is_staff):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("Access Denied: Administrators only.")
        
    # Base queryset
    employees = Employee.objects.all().order_by('-created_at')
    
    # Filtering parameters
    search_query = request.GET.get('search', '').strip()
    dept_filter = request.GET.get('department', '').strip()
    status_filter = request.GET.get('status', '').strip()
    min_salary = request.GET.get('min_salary', '').strip()
    max_salary = request.GET.get('max_salary', '').strip()
    sort_by = request.GET.get('sort', '').strip()
    
    if search_query:
        employees = employees.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(employee_id__icontains=search_query) |
            Q(job_title__icontains=search_query)
        )
        
    if dept_filter:
        employees = employees.filter(department=dept_filter)
        
    if status_filter:
        employees = employees.filter(status=status_filter)
        
    if min_salary:
        try:
            employees = employees.filter(salary__gte=float(min_salary))
        except (ValueError, TypeError):
            pass
            
    if max_salary:
        try:
            employees = employees.filter(salary__lte=float(max_salary))
        except (ValueError, TypeError):
            pass
        
    if sort_by:
        if sort_by == 'salary_asc':
            employees = employees.order_by('salary')
        elif sort_by == 'salary_desc':
            employees = employees.order_by('-salary')
        elif sort_by == 'hire_date_asc':
            employees = employees.order_by('hire_date')
        elif sort_by == 'hire_date_desc':
            employees = employees.order_by('-hire_date')
        elif sort_by == 'name_asc':
            employees = employees.order_by('first_name', 'last_name')
        elif sort_by == 'name_desc':
            employees = employees.order_by('-first_name', '-last_name')

    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="employees_export.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Employee ID', 'First Name', 'Last Name', 'Email', 'Phone', 'Job Title', 'Department', 'Salary', 'Hire Date', 'Status'])
    
    for emp in employees:
        writer.writerow([
            emp.employee_id,
            emp.first_name,
            emp.last_name,
            emp.email,
            emp.phone,
            emp.job_title,
            emp.department,
            emp.salary,
            emp.hire_date.strftime('%Y-%m-%d'),
            emp.status
        ])
        
    return response

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from datetime import datetime

@login_required
def generate_employee_pdf(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    
    is_admin = request.user.is_superuser or request.user.is_staff
    is_owner = hasattr(request.user, 'employee_profile') and request.user.employee_profile == employee
    if not (is_admin or is_owner):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("Access Denied: You can only generate your own PDF profile.")
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="profile_{employee.employee_id}.pdf"'
    
    # Create reportlab canvas document layout
    doc = SimpleDocTemplate(response, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    story = []
    styles = getSampleStyleSheet()
    
    primary_color = colors.HexColor("#6366f1")
    text_dark = colors.HexColor("#1f2937")
    text_light = colors.HexColor("#4b5563")
    bg_light = colors.HexColor("#f3f4f6")
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=24,
        textColor=primary_color,
        spaceAfter=6
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        textColor=text_light,
        spaceAfter=20
    )
    
    section_title_style = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        textColor=primary_color,
        spaceAfter=10,
        spaceBefore=15
    )
    
    body_style = ParagraphStyle(
        'BodyTextDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        textColor=text_dark,
        leading=14
    )
    
    label_style = ParagraphStyle(
        'LabelText',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        textColor=text_light
    )
    
    story.append(Paragraph("EMPLOYEE RECORD PROFILE", title_style))
    story.append(Paragraph(f"Generated on {datetime.now().strftime('%B %d, %Y, %I:%M %p')}", subtitle_style))
    story.append(Spacer(1, 10))
    
    data = [
        [Paragraph("Employee ID", label_style), Paragraph(employee.employee_id, body_style),
         Paragraph("Status", label_style), Paragraph(employee.status, body_style)],
         
        [Paragraph("Full Name", label_style), Paragraph(f"{employee.first_name} {employee.last_name}", body_style),
         Paragraph("Department", label_style), Paragraph(employee.department, body_style)],
         
        [Paragraph("Job Title", label_style), Paragraph(employee.job_title, body_style),
         Paragraph("Annual Salary", label_style), Paragraph(f"Rs. {float(employee.salary):,.2f}", body_style)],
         
        [Paragraph("Email Address", label_style), Paragraph(employee.email, body_style),
         Paragraph("Hire Date", label_style), Paragraph(employee.hire_date.strftime('%B %d, %Y'), body_style)],
         
        [Paragraph("Phone Number", label_style), Paragraph(employee.phone, body_style),
         Paragraph("", label_style), Paragraph("", body_style)]
    ]
    
    t = Table(data, colWidths=[100, 160, 100, 160])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), bg_light),
        ('PADDING', (0,0), (-1,-1), 10),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LINEBELOW', (0,0), (-1,-2), 0.5, colors.HexColor("#e5e7eb")),
    ]))
    
    story.append(t)
    story.append(Spacer(1, 20))
    
    story.append(Paragraph("Professional Notes & Biography", section_title_style))
    if employee.notes:
        story.append(Paragraph(employee.notes.replace('\n', '<br/>'), body_style))
    else:
        story.append(Paragraph("<i>No biography notes added for this employee profile.</i>", body_style))
        
    doc.build(story)
    
    ActivityLog.objects.create(
        user=request.user,
        action_type='Update',
        description=f"Generated PDF Profile Sheet for: {employee.first_name} {employee.last_name} ({employee.employee_id})."
    )
    
    return response

@login_required
def import_employees_csv(request):
    if not (request.user.is_superuser or request.user.is_staff):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("Access Denied: Administrators only.")
        
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        
        if not csv_file.name.endswith('.csv'):
            messages.error(request, "Please upload a valid CSV file (.csv extension).")
            return redirect('import_employees_csv')
            
        try:
            file_data = csv_file.read().decode('utf-8').splitlines()
            reader = csv.reader(file_data)
            
            raw_header = next(reader)
            header = [h.strip().lower() for h in raw_header]
            
            # Detect starting index / offset
            has_emp_id = False
            if 'employee id' in header or 'employee_id' in header or len(header) >= 10:
                has_emp_id = True
                
            offset = 1 if has_emp_id else 0
            required_cols = 9 + offset
            
            if len(header) < required_cols:
                messages.error(request, f"CSV structure mismatch. Expected at least {required_cols} columns.")
                return redirect('import_employees_csv')
                
            success_count = 0
            error_rows = []
            
            for index, row in enumerate(reader, start=2):
                if not row or len(row) < required_cols:
                    continue
                    
                first_name = row[offset + 0].strip()
                last_name = row[offset + 1].strip()
                email = row[offset + 2].strip()
                phone = row[offset + 3].strip()
                job_title = row[offset + 4].strip()
                department = row[offset + 5].strip()
                salary_str = row[offset + 6].strip()
                hire_date_str = row[offset + 7].strip()
                status = row[offset + 8].strip()
                
                if not (first_name and last_name and email and job_title and salary_str and hire_date_str):
                    error_rows.append(f"Row {index}: Missing required fields.")
                    continue
                    
                if Employee.objects.filter(email=email).exists():
                    error_rows.append(f"Row {index}: Email '{email}' is already registered.")
                    continue
                    
                try:
                    salary = float(salary_str)
                except ValueError:
                    error_rows.append(f"Row {index}: Invalid salary value '{salary_str}'.")
                    continue
                    
                # Support multiple date formats dynamically
                from datetime import datetime
                hire_date = None
                for fmt in ('%Y-%m-%d', '%d-%m-%Y', '%m-%d-%Y'):
                    try:
                        hire_date = datetime.strptime(hire_date_str, fmt).date()
                        break
                    except ValueError:
                        continue
                        
                if not hire_date:
                    error_rows.append(f"Row {index}: Invalid date '{hire_date_str}' (expected YYYY-MM-DD or DD-MM-YYYY).")
                    continue
                    
                employee = Employee.objects.create(
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    phone=phone,
                    job_title=job_title,
                    department=department,
                    salary=salary,
                    hire_date=hire_date,
                    status=status
                )
                try:
                    create_employee_user_account(employee, request)
                except Exception as e:
                    print(f"Error creating user account in import: {e}")
                success_count += 1
                
            if success_count > 0:
                messages.success(request, f"Successfully imported {success_count} employee records!")
                ActivityLog.objects.create(
                    user=request.user,
                    action_type='Import',
                    description=f"Imported {success_count} employee profiles from CSV upload."
                )
            
            if error_rows:
                for err in error_rows[:5]:
                    messages.error(request, err)
                if len(error_rows) > 5:
                    messages.error(request, f"...and {len(error_rows) - 5} more row errors.")
                    
            next_url = request.GET.get('next', 'dashboard')
            if not (next_url.startswith('/') or next_url == 'dashboard'):
                next_url = 'dashboard'
            return redirect(next_url)
            
        except Exception as e:
            messages.error(request, f"Error processing CSV: {str(e)}")
            next_url = request.GET.get('next', '')
            if next_url:
                return redirect(f'/import/csv/?next={next_url}')
            return redirect('import_employees_csv')
            
    return render(request, 'employees/import_csv.html')

@login_required
def department_view(request, dept_name):
    if not (request.user.is_superuser or request.user.is_staff):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("Access Denied: Administrators only.")
        
    valid_depts = [code for code, name in Employee.DEPARTMENT_CHOICES]
    if dept_name not in valid_depts:
        messages.error(request, f"Department '{dept_name}' does not exist.")
        return redirect('dashboard')
        
    dept_employees = Employee.objects.filter(department=dept_name).order_by('-created_at')
    headcount = dept_employees.count()
    avg_salary = dept_employees.aggregate(Avg('salary'))['salary__avg'] or 0
    active_count = dept_employees.filter(status='Active').count()
    on_leave_count = dept_employees.filter(status='On Leave').count()
    
    # Department tasks metrics
    total_tasks = EmployeeTask.objects.filter(employee__department=dept_name).count()
    completed_tasks = EmployeeTask.objects.filter(employee__department=dept_name, status='Completed').count()
    task_completion_rate = int(completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    
    dept_label = next((label for code, label in Employee.DEPARTMENT_CHOICES if code == dept_name), dept_name)
    
    context = {
        'dept_name': dept_name,
        'dept_label': dept_label,
        'employees': dept_employees,
        'headcount': headcount,
        'avg_salary': avg_salary,
        'active_count': active_count,
        'on_leave_count': on_leave_count,
        'task_completion_rate': task_completion_rate,
        'completed_tasks': completed_tasks,
    }
    return render(request, 'employees/department_detail.html', context)

@login_required
def assign_task(request, pk):
    if not (request.user.is_superuser or request.user.is_staff):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("Access Denied: Administrators only.")
        
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        form = EmployeeTaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.employee = employee
            task.save()
            
            # Notify employee via Web Alert
            if employee.user:
                Notification.objects.create(
                    recipient=employee.user,
                    message=f"You have been assigned a new task: '{task.title}'."
                )
                # Send email
                subject = f"New Task Assigned: {task.title}"
                email_msg = (
                    f"Hi {employee.first_name},\n\n"
                    f"An administrator has assigned you a new task in Employee Hub.\n\n"
                    f"Task Title: {task.title}\n"
                    f"Description: {task.description}\n"
                    f"Due Date: {task.due_date.strftime('%Y-%m-%d')}\n\n"
                    f"Please log in to your portal to review details.\n\n"
                    f"Employee Hub"
                )
                try:
                    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None) or 'notifications@employeehub.com'
                    send_mail(subject, email_msg, from_email, [employee.email], fail_silently=True)
                except Exception as e:
                    print(f"Error sending assignment email: {e}")
            
            ActivityLog.objects.create(
                user=request.user,
                action_type='Create',
                description=f"Assigned task '{task.title}' to employee {employee.first_name} {employee.last_name}."
            )
            messages.success(request, f"Task '{task.title}' successfully assigned to {employee.first_name}!")
            return redirect('employee_detail', pk=employee.pk)
    else:
        form = EmployeeTaskForm()
    return render(request, 'employees/task_form.html', {'form': form, 'employee': employee, 'title': 'Assign New Task'})

@login_required
def evaluate_task(request, task_id):
    if not (request.user.is_superuser or request.user.is_staff):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("Access Denied: Administrators only.")
        
    task = get_object_or_404(EmployeeTask, pk=task_id)
    employee = task.employee
    if request.method == 'POST':
        form = EmployeeTaskEvaluationForm(request.POST, instance=task)
        if form.is_valid():
            task = form.save()
            
            # Notify employee via Web Alert
            if employee.user:
                Notification.objects.create(
                    recipient=employee.user,
                    message=f"Your task '{task.title}' has been evaluated. Rating: {task.rating} Stars, Grade: {task.grade}."
                )
                # Send email
                subject = f"Task Evaluated: {task.title}"
                email_msg = (
                    f"Hi {employee.first_name},\n\n"
                    f"Your recently submitted task has been evaluated by an administrator.\n\n"
                    f"Task: {task.title}\n"
                    f"Rating: {task.rating} Stars\n"
                    f"Grade: {task.grade}\n"
                    f"Feedback: {task.feedback}\n\n"
                    f"Employee Hub"
                )
                    
                try:
                    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None) or 'notifications@employeehub.com'
                    send_mail(subject, email_msg, from_email, [employee.email], fail_silently=True)
                except Exception as e:
                    print(f"Error sending evaluation email: {e}")
            
            rating_stars = f"{task.rating} Star{'s' if task.rating > 1 else ''}" if task.rating else "No Stars"
            ActivityLog.objects.create(
                user=request.user,
                action_type='Update',
                description=f"Evaluated task '{task.title}' for {employee.first_name} {employee.last_name}. Rating: {rating_stars}, Grade: {task.grade}."
            )
            messages.success(request, f"Evaluation submitted for task '{task.title}'!")
            return redirect('employee_detail', pk=employee.pk)
    else:
        form = EmployeeTaskEvaluationForm(instance=task)
    return render(request, 'employees/task_evaluate.html', {'form': form, 'task': task, 'employee': employee, 'title': 'Evaluate Task Performance'})

@login_required
def portal_view(request):
    if not hasattr(request.user, 'employee_profile'):
        if request.user.is_superuser or request.user.is_staff:
            return redirect('dashboard')
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("Access Denied: No employee profile is linked to your user account.")
        
    employee = request.user.employee_profile
    tasks = employee.tasks.all().order_by('-due_date')
    total_tasks = tasks.count()
    completed_tasks = tasks.filter(status='Completed').count()
    completion_rate = int((completed_tasks / total_tasks * 100)) if total_tasks > 0 else 0
    avg_rating = tasks.filter(status='Completed', rating__isnull=False).aggregate(Avg('rating'))['rating__avg'] or 0
    
    context = {
        'employee': employee,
        'tasks': tasks,
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'completion_rate': completion_rate,
        'avg_rating': round(float(avg_rating), 1),
        'stars_range': range(1, 6),
    }
    return render(request, 'employees/portal.html', context)

@login_required
def update_task_status(request, task_id):
    task = get_object_or_404(EmployeeTask, pk=task_id)
    employee = task.employee
    
    # Authorize: Owner or Admin
    is_admin = request.user.is_superuser or request.user.is_staff
    is_owner = hasattr(request.user, 'employee_profile') and request.user.employee_profile == employee
    if not (is_admin or is_owner):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("Access Denied: You cannot modify this task.")
        
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in [choice[0] for choice in EmployeeTask.STATUS_CHOICES]:
            if not is_admin and new_status != 'In Progress':
                messages.error(request, "Task completions must be submitted with a work attachment file.")
                return redirect('employee_portal')
            old_status = task.status
            task.status = new_status
            task.save()
            
            # Log action
            ActivityLog.objects.create(
                user=request.user,
                action_type='Update',
                description=f"Task '{task.title}' status updated from '{old_status}' to '{new_status}'."
            )
            
            # If updated by employee, notify administrators
            if not is_admin:
                admins = User.objects.filter(is_superuser=True) | User.objects.filter(is_staff=True)
                for admin in admins.distinct():
                    Notification.objects.create(
                        recipient=admin,
                        message=f"Employee {employee.first_name} {employee.last_name} marked task '{task.title}' as '{new_status}'."
                    )
                    # Send console email
                    if admin.email:
                        subject = f"Task Status Update: {task.title}"
                        email_msg = (
                            f"Administrator,\n\n"
                            f"Employee {employee.first_name} {employee.last_name} has updated the status of their assigned task.\n\n"
                            f"Task: {task.title}\n"
                            f"Old Status: {old_status}\n"
                            f"New Status: {new_status}\n\n"
                            f"Log in to review: http://{request.get_host()}/employee/{employee.pk}/\n"
                        )
                        try:
                            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None) or 'notifications@employeehub.com'
                            send_mail(subject, email_msg, from_email, [admin.email], fail_silently=True)
                        except Exception as e:
                            print(f"Error sending status update email: {e}")
            
            messages.success(request, f"Task '{task.title}' status successfully set to '{new_status}'!")
            
    if request.user.is_superuser or request.user.is_staff:
        return redirect('employee_detail', pk=employee.pk)
    return redirect('employee_portal')

@login_required
def bulk_assign_task(request):
    if not (request.user.is_superuser or request.user.is_staff):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("Access Denied: Administrators only.")
        
    dept_name = request.GET.get('department') or request.POST.get('department')
    
    if request.method == 'POST':
        form = BulkTaskAssignmentForm(request.POST)
        if dept_name:
            form.fields['employees'].queryset = Employee.objects.filter(department=dept_name, status='Active')
            
        if form.is_valid():
            title = form.cleaned_data['title']
            description = form.cleaned_data['description']
            due_date = form.cleaned_data['due_date']
            employees = form.cleaned_data['employees']
            
            assigned_names = []
            for employee in employees:
                task = EmployeeTask.objects.create(
                    employee=employee,
                    title=title,
                    description=description,
                    due_date=due_date,
                    status='Pending'
                )
                assigned_names.append(f"{employee.first_name} {employee.last_name}")
                
                # Notify employee
                if employee.user:
                    Notification.objects.create(
                        recipient=employee.user,
                        message=f"You have been assigned a new task: '{title}'."
                    )
                    # Send email
                    subject = f"New Task Assigned: {title}"
                    email_msg = (
                        f"Hi {employee.first_name},\n\n"
                        f"An administrator has assigned you a new task: '{title}' in Employee Hub.\n\n"
                        f"Description: {description}\n"
                        f"Due Date: {due_date.strftime('%Y-%m-%d')}\n\n"
                        f"Log in to your portal to submit updates: http://{request.get_host()}/portal/\n"
                    )
                    try:
                        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None) or 'notifications@employeehub.com'
                        send_mail(subject, email_msg, from_email, [employee.email], fail_silently=True)
                    except Exception as e:
                        print(f"Error sending bulk task email: {e}")
            
            ActivityLog.objects.create(
                user=request.user,
                action_type='Create',
                description=f"Bulk-assigned task '{title}' to {len(employees)} employees: {', '.join(assigned_names)}."
            )
            messages.success(request, f"Task successfully bulk-assigned to {len(employees)} employees!")
            if dept_name:
                return redirect('department_view', dept_name=dept_name)
            return redirect('dashboard')
    else:
        form = BulkTaskAssignmentForm()
        if dept_name:
            form.fields['employees'].queryset = Employee.objects.filter(department=dept_name, status='Active')
            
    return render(request, 'employees/bulk_assign_task.html', {
        'form': form, 
        'title': f'Bulk Assign Task ({dept_name})' if dept_name else 'Bulk Assign Task',
        'dept_name': dept_name
    })

@login_required
def mark_notifications_read(request):
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    messages.success(request, "All notifications marked as read.")
    next_url = request.GET.get('next', '')
    if next_url.startswith('/') or next_url == 'dashboard':
        return redirect(next_url)
    if request.user.is_superuser or request.user.is_staff:
        return redirect('dashboard')
    return redirect('employee_portal')

class EmployeePasswordChangeView(SuccessMessageMixin, PasswordChangeView):
    template_name = 'employees/password_change.html'
    success_url = '/portal/'
    success_message = "Your password has been successfully updated!"

@login_required
def submit_task_work(request, task_id):
    task = get_object_or_404(EmployeeTask, pk=task_id)
    # Ensure they have an employee profile
    if not hasattr(request.user, 'employee_profile'):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("Access Denied: You must be an employee to submit work.")
    
    employee = request.user.employee_profile
    if task.employee != employee:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("Access Denied: You cannot submit work for this task.")
        
    if request.method == 'POST':
        form = EmployeeTaskSubmissionForm(request.POST, request.FILES, instance=task)
        if form.is_valid():
            task = form.save(commit=False)
            task.status = 'Pending Review'
            task.save()
            
            # Log action
            ActivityLog.objects.create(
                user=request.user,
                action_type='Update',
                description=f"Submitted task '{task.title}' for review with work attachment."
            )
            
            # Notify admins
            admins = User.objects.filter(is_superuser=True) | User.objects.filter(is_staff=True)
            for admin in admins.distinct():
                Notification.objects.create(
                    recipient=admin,
                    message=f"Employee {employee.first_name} {employee.last_name} submitted task '{task.title}' for review."
                )
                # Send console email
                if admin.email:
                    subject = f"Review Request: {task.title}"
                    email_msg = (
                        f"Administrator,\n\n"
                        f"Employee {employee.first_name} {employee.last_name} has submitted work for task review.\n\n"
                        f"Task: {task.title}\n"
                        f"Attachment Name: {task.work_submission.name}\n"
                        f"Notes: {task.submission_notes or 'No notes provided.'}\n\n"
                        f"Log in to review: http://{request.get_host()}/employee/{employee.pk}/\n"
                    )
                    try:
                        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None) or 'notifications@employeehub.com'
                        send_mail(subject, email_msg, from_email, [admin.email], fail_silently=True)
                    except Exception as e:
                        print(f"Error sending review request email: {e}")
            
            messages.success(request, f"Task '{task.title}' successfully submitted for review!")
            return redirect('employee_portal')
    else:
        form = EmployeeTaskSubmissionForm(instance=task)
        
    return render(request, 'employees/task_submit.html', {'form': form, 'task': task})
