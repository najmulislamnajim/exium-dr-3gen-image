from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import Territory

class Command(BaseCommand):
    help = 'Create users for each territory and an admin user'

    def handle(self, *args, **kwargs):
        # Create users for territories
        territories = Territory.objects.all()
        default_password = '123456'
        for territory in territories:
            username = territory.territory
            if not User.objects.filter(username=username).exists():
                User.objects.create_user(
                    username=username,
                    password=default_password
                )
                self.stdout.write(self.style.SUCCESS(f'Created user for {username}'))
            else:
                self.stdout.write(f'User {username} already exists')

        # Create admin user
        admin_username = 'admin'
        admin_password = 'rpl@123'
        if not User.objects.filter(username=admin_username).exists():
            User.objects.create_superuser(
                username=admin_username,
                password=admin_password,
                email='admin@example.com'
            )
            self.stdout.write(self.style.SUCCESS('Created admin user'))
        else:
            self.stdout.write('Admin user already exists')