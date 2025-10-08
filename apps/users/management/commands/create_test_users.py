from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.users.models import UserProfile
from apps.branches.models import Branch


class Command(BaseCommand):
    help = 'Create test users for the system'

    def handle(self, *args, **options):
        # Create test branch if not exists
        branch, created = Branch.objects.get_or_create(
            code='TEST001',
            defaults={
                'name': 'Test Branch',
                'type': 'main',
                'category': 'A',
                'status': 'active',
                'address': 'Riyadh, Saudi Arabia',
                'city': 'Riyadh',
                'region': 'riyadh',
                'phone': '+966501234567',
                'email': 'test@company.com',
                'capacity': 50,
                'working_days': ['saturday', 'sunday', 'monday', 'tuesday', 'wednesday', 'thursday']
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created test branch: {branch.name}'))
        else:
            self.stdout.write(f'Test branch already exists: {branch.name}')
        
        # Test users data
        test_users = [
            {
                'username': 'admin',
                'password': 'admin123',
                'first_name': 'Admin',
                'last_name': 'User',
                'email': 'admin@company.com',
                'role': 'super_admin',
                'branch': None,
                'phone': '+966501234567',
                'position': 'General Manager',
                'department': 'operations'
            },
            {
                'username': 'manager1',
                'password': 'password123',
                'first_name': 'Manager',
                'last_name': 'User',
                'email': 'manager1@company.com',
                'role': 'branch_manager',
                'branch': branch,
                'phone': '+966501234568',
                'position': 'Branch Manager',
                'department': 'operations'
            },
            {
                'username': 'coordinator1',
                'password': 'password123',
                'first_name': 'Coordinator',
                'last_name': 'User',
                'email': 'coordinator1@company.com',
                'role': 'coordinator',
                'branch': None,
                'phone': '+966501234569',
                'position': 'Coordinator',
                'department': 'operations'
            },
            {
                'username': 'employee1',
                'password': 'password123',
                'first_name': 'Employee',
                'last_name': 'User',
                'email': 'employee1@company.com',
                'role': 'employee',
                'branch': branch,
                'phone': '+966501234570',
                'position': 'Employee',
                'department': 'operations'
            }
        ]
        
        created_count = 0
        
        for user_data in test_users:
            # Get or create user
            user, user_created = User.objects.get_or_create(
                username=user_data['username'],
                defaults={
                    'first_name': user_data['first_name'],
                    'last_name': user_data['last_name'],
                    'email': user_data['email'],
                    'is_staff': True,
                    'is_superuser': (user_data['role'] == 'super_admin')
                }
            )
            
            # Set password
            user.set_password(user_data['password'])
            user.first_name = user_data['first_name']
            user.last_name = user_data['last_name']
            user.email = user_data['email']
            user.is_staff = True
            user.is_superuser = (user_data['role'] == 'super_admin')
            user.save()
            
            # Update or create profile
            if hasattr(user, 'profile'):
                profile = user.profile
            else:
                profile = UserProfile.objects.create(user=user)
            
            profile.role = user_data['role']
            profile.phone = user_data['phone']
            profile.position = user_data['position']
            profile.department = user_data['department']
            profile.branch = user_data['branch']
            profile.work_hours = 8
            profile.work_days = 6
            profile.status = 'active'
            profile.save()
            
            created_count += 1
            status = "Created" if user_created else "Updated"
            role_display = dict(UserProfile.ROLE_CHOICES)[profile.role]
            self.stdout.write(f'{status} user: {user.get_full_name()} ({user_data["username"]}) - {role_display}')
        
        self.stdout.write(self.style.SUCCESS(f'\nProcessed {created_count} users'))
        
        self.stdout.write('\nLogin credentials:')
        self.stdout.write('=' * 50)
        for user_data in test_users:
            self.stdout.write(f'User: {user_data["first_name"]} {user_data["last_name"]}')
            self.stdout.write(f'   Username: {user_data["username"]}')
            self.stdout.write(f'   Password: {user_data["password"]}')
            self.stdout.write(f'   Role: {dict(UserProfile.ROLE_CHOICES)[user_data["role"]]}')
            self.stdout.write('-' * 30)
        
        self.stdout.write(self.style.SUCCESS('\nSuccessfully processed all test users!'))
        self.stdout.write('You can now login at: http://127.0.0.1:8000/')
