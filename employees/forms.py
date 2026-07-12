from django import forms
from .models import Employee, EmployeeTask

class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = [
            'first_name', 'last_name', 'email', 'phone', 
            'job_title', 'department', 'salary', 'hire_date', 
            'status', 'notes'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter first name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter last name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter email address'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter phone number'
            }),
            'job_title': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter job title (e.g., Lead Developer)'
            }),
            'department': forms.Select(attrs={
                'class': 'form-select'
            }),
            'salary': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter annual salary',
                'step': '0.01'
            }),
            'hire_date': forms.DateInput(attrs={
                'class': 'form-input',
                'type': 'date'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-textarea',
                'placeholder': 'Add any additional notes, skills, or background details...',
                'rows': 4
            }),
        }

class EmployeeTaskForm(forms.ModelForm):
    class Meta:
        model = EmployeeTask
        fields = ['title', 'description', 'due_date', 'status']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Task Title'}),
            'description': forms.Textarea(attrs={'class': 'form-textarea', 'placeholder': 'Detailed description of the task...', 'rows': 3}),
            'due_date': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

class EmployeeTaskEvaluationForm(forms.ModelForm):
    class Meta:
        model = EmployeeTask
        fields = ['status', 'rating', 'grade', 'feedback']
        widgets = {
            'status': forms.Select(choices=[('Completed', 'Completed'), ('Failed', 'Failed')], attrs={'class': 'form-select'}),
            'rating': forms.NumberInput(attrs={'class': 'form-input', 'min': '1', 'max': '5', 'placeholder': 'Rating (1-5 Stars)'}),
            'grade': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. A+, B, C'}),
            'feedback': forms.Textarea(attrs={'class': 'form-textarea', 'placeholder': 'Provide feedback on employee work...', 'rows': 3}),
        }

class EmployeeMultipleChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        return f"{obj.first_name} {obj.last_name} | {obj.job_title} | {obj.email}"

class BulkTaskAssignmentForm(forms.Form):
    title = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Task Title'}),
        max_length=200
    )
    description = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-textarea', 'placeholder': 'Detailed description of the task...', 'rows': 3}),
        required=False
    )
    due_date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-input', 'type': 'date'})
    )
    employees = EmployeeMultipleChoiceField(
        queryset=Employee.objects.filter(status='Active'),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-checkbox-list'}),
        help_text="Select one or more employees to assign this task to."
    )

class EmployeeTaskSubmissionForm(forms.ModelForm):
    class Meta:
        model = EmployeeTask
        fields = ['work_submission', 'submission_notes']
        widgets = {
            'work_submission': forms.FileInput(attrs={'class': 'form-input'}),
            'submission_notes': forms.Textarea(attrs={'class': 'form-textarea', 'placeholder': 'Write any notes about your work submission...', 'rows': 3}),
        }
