from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from bus_route.models import Schedule


class Depot(models.Model):
    depot_id = models.AutoField(primary_key=True)
    depot_name = models.CharField(max_length=100)
    depot_code = models.CharField(max_length=20, unique=True)
    location = models.CharField(max_length=200)
    contact_number = models.CharField(max_length=15, blank=True)
    is_active = models.BooleanField(default=True)
    created_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.depot_code} - {self.depot_name}"


class DepotUser(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('staff', 'Staff'),
    ]
    
    depot_user_id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=50, unique=True)
    password_hash = models.CharField(max_length=128)
    depot = models.ForeignKey(Depot, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='staff')
    is_active = models.BooleanField(default=True)
    created_date = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)

    def set_password(self, raw_password):
        self.password_hash = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password_hash)

    def __str__(self):
        return f"{self.username} ({self.depot.depot_code})"


class Employee(models.Model):
    ROLE_CHOICES = [
        ('conductor', 'Conductor'),
        ('driver', 'Driver'),
    ]
    
    employee_id = models.CharField(max_length=20, primary_key=True)
    employee_name = models.CharField(max_length=100)
    depot = models.ForeignKey(Depot, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    phone_number = models.CharField(max_length=15)
    license_number = models.CharField(max_length=50, blank=True, null=True)
    joining_date = models.DateField()
    is_active = models.BooleanField(default=True)
    created_date = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.role == 'conductor':
            self.license_number = None
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.employee_id} - {self.employee_name} ({self.role})"


class ScheduleAssignment(models.Model):
    STATUS_CHOICES = [
        ('assigned', 'Assigned'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    assignment_id = models.AutoField(primary_key=True)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    schedule_no = models.CharField(max_length=20)
    trip_no = models.IntegerField()
    route_no = models.CharField(max_length=20)
    date = models.DateField()
    assigned_by = models.ForeignKey(DepotUser, on_delete=models.CASCADE)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='assigned')
    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ['employee', 'date', 'schedule_no', 'trip_no']

    def get_schedule_info(self):
        try:
            return Schedule.objects.get(schedule_no=self.schedule_no, trip_no=self.trip_no)
        except Schedule.DoesNotExist:
            return None

    def __str__(self):
        return f"{self.employee.employee_name} - {self.schedule_no}/{self.trip_no} on {self.date}"


class Attendance(models.Model):
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('half_day', 'Half Day'),
    ]
    
    attendance_id = models.AutoField(primary_key=True)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    schedule_assignment = models.ForeignKey(ScheduleAssignment, on_delete=models.CASCADE, null=True, blank=True)
    date = models.DateField()
    check_in_time = models.TimeField(null=True, blank=True)
    check_out_time = models.TimeField(null=True, blank=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='absent')
    marked_by = models.ForeignKey(DepotUser, on_delete=models.CASCADE)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['employee', 'date', 'schedule_assignment']

    def __str__(self):
        return f"{self.employee.employee_name} - {self.date} ({self.status})"
