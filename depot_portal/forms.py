from django import forms
from django.core.exceptions import ValidationError
from bus_route.models import Schedule
from .models import Employee, ScheduleAssignment, Attendance, Depot


class DepotLoginForm(forms.Form):
    username = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password'
        })
    )


class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ['employee_id', 'employee_name', 'role', 'phone_number', 'license_number', 'joining_date']
        widgets = {
            'employee_id': forms.TextInput(attrs={'class': 'form-control'}),
            'employee_name': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'license_number': forms.TextInput(attrs={'class': 'form-control'}),
            'joining_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        license_number = cleaned_data.get('license_number')

        if role == 'driver' and not license_number:
            raise ValidationError("License number is required for drivers.")
        
        return cleaned_data


class ScheduleAssignmentForm(forms.ModelForm):
    class Meta:
        model = ScheduleAssignment
        fields = ['employee', 'schedule_no', 'trip_no', 'route_no', 'date', 'notes']
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-control'}),
            'schedule_no': forms.Select(attrs={'class': 'form-control'}),
            'trip_no': forms.Select(attrs={'class': 'form-control'}),
            'route_no': forms.Select(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        depot = kwargs.pop('depot', None)
        super().__init__(*args, **kwargs)
        
        if depot:
            self.fields['employee'].queryset = Employee.objects.filter(
                depot=depot, 
                is_active=True
            )
        
        # Populate schedule choices from Schedule model
        schedule_choices = Schedule.objects.values_list('schedule_no', flat=True).distinct()
        self.fields['schedule_no'].widget = forms.Select(
            choices=[('', 'Select Schedule')] + [(s, s) for s in schedule_choices],
            attrs={'class': 'form-control', 'id': 'id_schedule_no'}
        )
        
        trip_choices = Schedule.objects.values_list('trip_no', flat=True).distinct()
        self.fields['trip_no'].widget = forms.Select(
            choices=[('', 'Select Trip')] + [(t, t) for t in trip_choices],
            attrs={'class': 'form-control', 'id': 'id_trip_no'}
        )
        
        route_choices = Schedule.objects.values_list('route_no', flat=True).distinct()
        self.fields['route_no'].widget = forms.Select(
            choices=[('', 'Select Route')] + [(r, r) for r in route_choices],
            attrs={'class': 'form-control', 'id': 'id_route_no'}
        )

    def clean(self):
        cleaned_data = super().clean()
        schedule_no = cleaned_data.get('schedule_no')
        trip_no = cleaned_data.get('trip_no')
        route_no = cleaned_data.get('route_no')
        employee = cleaned_data.get('employee')
        date = cleaned_data.get('date')

        # Validate that the schedule combination exists
        if schedule_no and trip_no and route_no:
            if not Schedule.objects.filter(
                schedule_no=schedule_no,
                trip_no=trip_no,
                route_no=route_no
            ).exists():
                raise ValidationError("Invalid schedule combination.")

        # Check for duplicate assignments (same employee, date, schedule, and trip)
        if employee and date and schedule_no and trip_no:
            existing = ScheduleAssignment.objects.filter(
                employee=employee,
                date=date,
                schedule_no=schedule_no,
                trip_no=trip_no
            )
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                raise ValidationError("This employee is already assigned to this specific trip on this date.")

        return cleaned_data


class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ['employee', 'schedule_assignment', 'date', 'check_in_time', 'check_out_time', 'status', 'notes']
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-control'}),
            'schedule_assignment': forms.Select(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'check_in_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'check_out_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        depot = kwargs.pop('depot', None)
        super().__init__(*args, **kwargs)
        
        if depot:
            self.fields['employee'].queryset = Employee.objects.filter(
                depot=depot, 
                is_active=True
            )
            self.fields['schedule_assignment'].queryset = ScheduleAssignment.objects.filter(
                employee__depot=depot
            ).select_related('employee').order_by('-date', 'employee__employee_name')

    def clean(self):
        cleaned_data = super().clean()
        employee = cleaned_data.get('employee')
        date = cleaned_data.get('date')
        schedule_assignment = cleaned_data.get('schedule_assignment')

        # Check for duplicate attendance records
        if employee and date and schedule_assignment:
            existing = Attendance.objects.filter(
                employee=employee, 
                date=date, 
                schedule_assignment=schedule_assignment
            )
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                raise ValidationError("Attendance for this employee and assignment on this date already exists.")

        return cleaned_data