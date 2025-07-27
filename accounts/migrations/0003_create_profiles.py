from django.db import migrations

def create_profiles(apps, schema_editor):
    User = apps.get_model('accounts', 'User')
    Profile = apps.get_model('accounts', 'Profile')
    
    for user in User.objects.all():
        Profile.objects.get_or_create(user=user)

class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0002_profile'),
    ]

    operations = [
        migrations.RunPython(create_profiles),
    ] 