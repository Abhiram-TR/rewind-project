from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages

def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            # This saves the user information to the database
            user = form.save()
            # Log the user in after registration
            login(request, user)
            messages.success(request, f"Account created for {user.username}!")
            return redirect('login_app:main_home')  # Redirect to your home page
        else:
            # Form validation errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = UserCreationForm()
    return render(request, 'login_app/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            # This authenticates against the database
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {username}!")
                return redirect('login_app:main_home')  # Redirect to your home page
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    return render(request, 'login_app/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, "You have successfully logged out.")
    return redirect('login_app:login')

# Step 4: Create a home view that shows authenticated user information
def home_view(request):
    return render(request, 'login_app/home.html')

def main_home_view(request):
    return render(request, 'login_app/main_home.html')
def dashboard_view(request):
    # You might want to add a login_required decorator to this view
    return render(request, 'login_app/dashboard.html')