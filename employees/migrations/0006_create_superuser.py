from django.db import migrations

def create_admin_user(apps, schema_editor):
    from django.contrib.auth.models import User
    # Use 'system_admin' to avoid any conflict with 'admin' in local tests
    if not User.objects.filter(username='system_admin').exists():
        User.objects.create_superuser('system_admin', 'system_admin@example.com', 'password123')

class Migration(migrations.Migration):

    dependencies = [
        ('employees', '0005_employeetask_submission_notes_and_more'),
    ]

    operations = [
        migrations.RunPython(create_admin_user),
    ]
