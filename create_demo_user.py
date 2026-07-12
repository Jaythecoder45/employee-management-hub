from django.contrib.auth.models import User

# Clear existing admin user if exists
User.objects.filter(username='admin').delete()

# Create superuser
admin_user = User.objects.create_superuser('admin', 'admin@company.com', 'password123')
admin_user.first_name = "System"
admin_user.last_name = "Administrator"
admin_user.save()

print("Successfully created demo admin user!")
print("Credentials:")
print("  Username: admin")
print("  Password: password123")
