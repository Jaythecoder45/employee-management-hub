from datetime import date
from employees.models import Employee

# Clear existing records
Employee.objects.all().delete()

employees_data = [
    {
        "first_name": "Alexander",
        "last_name": "Wright",
        "email": "a.wright@company.com",
        "phone": "+1 (555) 019-2834",
        "job_title": "Lead Software Engineer",
        "department": "Engineering",
        "salary": 115000.00,
        "hire_date": date(2023, 6, 12),
        "status": "Active",
        "notes": "Team lead for the Core Platform squad. Specialized in Python, Django, and cloud infrastructure."
    },
    {
        "first_name": "Sarah",
        "last_name": "Jenkins",
        "email": "s.jenkins@company.com",
        "phone": "+1 (555) 014-9982",
        "job_title": "UX Designer",
        "department": "Marketing",
        "salary": 85000.00,
        "hire_date": date(2024, 2, 18),
        "status": "Active",
        "notes": "Leads user research and interface designs for all customer-facing mobile and web applications."
    },
    {
        "first_name": "Marcus",
        "last_name": "Chen",
        "email": "m.chen@company.com",
        "phone": "+1 (555) 017-4829",
        "job_title": "Financial Analyst",
        "department": "Finance",
        "salary": 92000.00,
        "hire_date": date(2022, 10, 5),
        "status": "Active",
        "notes": "Handles quarterly forecasting, budget alignment, and corporate audit preparations."
    },
    {
        "first_name": "Elena",
        "last_name": "Rostova",
        "email": "e.rostova@company.com",
        "phone": "+1 (555) 012-3345",
        "job_title": "HR Manager",
        "department": "HR",
        "salary": 78000.00,
        "hire_date": date(2021, 4, 1),
        "status": "Active",
        "notes": "Head of employee relations, benefits administration, and onboarding strategy."
    },
    {
        "first_name": "David",
        "last_name": "Kim",
        "email": "d.kim@company.com",
        "phone": "+1 (555) 015-6671",
        "job_title": "DevOps Engineer",
        "department": "Engineering",
        "salary": 105000.00,
        "hire_date": date(2024, 8, 22),
        "status": "Active",
        "notes": "Responsible for CI/CD pipelines, containerization, and AWS server reliability."
    },
    {
        "first_name": "Olivia",
        "last_name": "Martinez",
        "email": "o.martinez@company.com",
        "phone": "+1 (555) 013-1122",
        "job_title": "Marketing Coordinator",
        "department": "Marketing",
        "salary": 65000.00,
        "hire_date": date(2025, 1, 15),
        "status": "On Leave",
        "notes": "Coordinates social campaigns and digital advertising schedules. Currently on maternity leave."
    },
    {
        "first_name": "Robert",
        "last_name": "Taylor",
        "email": "r.taylor@company.com",
        "phone": "+1 (555) 018-7744",
        "job_title": "Operations Director",
        "department": "Operations",
        "salary": 130000.00,
        "hire_date": date(2019, 11, 1),
        "status": "Active",
        "notes": "Oversees global supply chain, logistics partnerships, and physical office management."
    },
    {
        "first_name": "Emily",
        "last_name": "Watson",
        "email": "e.watson@company.com",
        "phone": "+1 (555) 011-5566",
        "job_title": "Sales Executive",
        "department": "Sales",
        "salary": 72000.00,
        "hire_date": date(2023, 3, 10),
        "status": "Inactive",
        "notes": "Managed mid-market software sales accounts. Departed company in June 2026."
    },
    {
        "first_name": "James",
        "last_name": "Anderson",
        "email": "j.anderson@company.com",
        "phone": "+1 (555) 016-8899",
        "job_title": "Technical Writer",
        "department": "Engineering",
        "salary": 70000.00,
        "hire_date": date(2025, 5, 20),
        "status": "Active",
        "notes": "Author of developer API references, internal architectural wikis, and user guides."
    },
    {
        "first_name": "Sophia",
        "last_name": "Patel",
        "email": "s.patel@company.com",
        "phone": "+1 (555) 019-2233",
        "job_title": "Talent Acquisition Specialist",
        "department": "HR",
        "salary": 68000.00,
        "hire_date": date(2024, 11, 12),
        "status": "Active",
        "notes": "Focuses on technical recruiting, sourcing engineers, and university internship programs."
    }
]

for item in employees_data:
    Employee.objects.create(**item)

print(f"Successfully seeded {len(employees_data)} employees!")
