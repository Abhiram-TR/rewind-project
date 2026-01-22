from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, timedelta
from depot_portal.models import Depot, DepotUser, Employee, ScheduleAssignment, Attendance


class Command(BaseCommand):
    help = 'Create sample depot data for testing'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample depot data...')
        
        # Create sample depots
        depot1, created = Depot.objects.get_or_create(
            depot_code='TVM001',
            defaults={
                'depot_name': 'Thiruvananthapuram Central Depot',
                'location': 'Thiruvananthapuram, Kerala',
                'contact_number': '0471-2345678',
            }
        )
        if created:
            self.stdout.write(f'Created depot: {depot1}')
        
        depot2, created = Depot.objects.get_or_create(
            depot_code='EKM002', 
            defaults={
                'depot_name': 'Ernakulam Bus Depot',
                'location': 'Ernakulam, Kerala',
                'contact_number': '0484-2567890',
            }
        )
        if created:
            self.stdout.write(f'Created depot: {depot2}')
        
        # Create depot users
        user1, created = DepotUser.objects.get_or_create(
            username='admin_tvm',
            defaults={
                'depot': depot1,
                'full_name': 'Admin Thiruvananthapuram',
                'role': 'admin',
            }
        )
        if created:
            user1.set_password('admin123')
            user1.save()
            self.stdout.write(f'Created user: {user1.username} (password: admin123)')
        
        user2, created = DepotUser.objects.get_or_create(
            username='staff_ekm',
            defaults={
                'depot': depot2,
                'full_name': 'Staff Ernakulam',
                'role': 'staff',
            }
        )
        if created:
            user2.set_password('staff123')
            user2.save()
            self.stdout.write(f'Created user: {user2.username} (password: staff123)')
        
        # Create sample employees
        emp1, created = Employee.objects.get_or_create(
            employee_id='EMP001',
            defaults={
                'employee_name': 'Ravi Kumar',
                'depot': depot1,
                'role': 'driver',
                'phone_number': '9876543210',
                'license_number': 'KL01DL123456',
                'joining_date': date.today() - timedelta(days=365),
            }
        )
        if created:
            self.stdout.write(f'Created employee: {emp1}')
        
        emp2, created = Employee.objects.get_or_create(
            employee_id='EMP002',
            defaults={
                'employee_name': 'Suresh Nair',
                'depot': depot1,
                'role': 'conductor',
                'phone_number': '9876543211',
                'joining_date': date.today() - timedelta(days=300),
            }
        )
        if created:
            self.stdout.write(f'Created employee: {emp2}')
        
        emp3, created = Employee.objects.get_or_create(
            employee_id='EMP003',
            defaults={
                'employee_name': 'Rajesh Menon',
                'depot': depot2,
                'role': 'driver',
                'phone_number': '9876543212',
                'license_number': 'KL07DL789012',
                'joining_date': date.today() - timedelta(days=200),
            }
        )
        if created:
            self.stdout.write(f'Created employee: {emp3}')
        
        # Create sample schedule assignments
        today = date.today()
        assignment1, created = ScheduleAssignment.objects.get_or_create(
            employee=emp1,
            date=today,
            schedule_no='SCH001',
            trip_no=1,
            defaults={
                'route_no': 'R001',
                'assigned_by': user1,
                'status': 'assigned',
                'notes': 'Morning shift assignment',
            }
        )
        if created:
            self.stdout.write(f'Created assignment: {assignment1}')
        
        # Create sample attendance records
        attendance1, created = Attendance.objects.get_or_create(
            employee=emp1,
            date=today,
            defaults={
                'schedule_assignment': assignment1,
                'check_in_time': timezone.now().time(),
                'status': 'present',
                'marked_by': user1,
                'notes': 'On time',
            }
        )
        if created:
            self.stdout.write(f'Created attendance: {attendance1}')
        
        attendance2, created = Attendance.objects.get_or_create(
            employee=emp2,
            date=today,
            defaults={
                'check_in_time': timezone.now().time(),
                'status': 'present',
                'marked_by': user1,
                'notes': 'On time',
            }
        )
        if created:
            self.stdout.write(f'Created attendance: {attendance2}')
        
        self.stdout.write(
            self.style.SUCCESS('Successfully created sample depot data!')
        )
        self.stdout.write('\n--- LOGIN CREDENTIALS ---')
        self.stdout.write('Depot Portal Login URL: http://127.0.0.1:8000/depot/login/')
        self.stdout.write('Username: admin_tvm | Password: admin123 (Thiruvananthapuram Admin)')
        self.stdout.write('Username: staff_ekm | Password: staff123 (Ernakulam Staff)')