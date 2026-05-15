"""
auth_views.py
-------------
Handles all authentication-related views:
  - register_view    – Sign-up form (AJAX + traditional POST)
  - login_view       – Login form  (AJAX + traditional POST)
  - logout_view      – Logout redirect
  - check_availability – AJAX endpoint used by the signup form
"""

import re

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse


def _is_ajax(request):
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'


# ─────────────────────────────────────────────
#  REGISTER
# ─────────────────────────────────────────────

def register_view(request):

    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':

        email    = request.POST.get('email',    '').strip()
        fullname = request.POST.get('fullname', '').strip()
        username = request.POST.get('username', '').strip().lower()
        password = request.POST.get('password', '')
        is_ajax  = _is_ajax(request)

        def err(msg, field=None):
            if is_ajax:
                return JsonResponse({'success': False, 'error': msg, 'field': field})
            messages.error(request, msg)
            return redirect('register')

        if not email:
            return err('Please enter your email.', 'email')
        if not fullname:
            return err('Please enter your full name.', 'fullname')
        if not username:
            return err('Please enter a username.', 'username')
        if not password:
            return err('Please enter a password.', 'password')
        if len(password) < 6:
            return err('Password must be at least 6 characters.', 'password')
        if not re.match(r'^[a-z0-9._]{3,30}$', username):
            return err('Username must be 3–30 chars: letters, numbers, . or _', 'username')
        if User.objects.filter(username=username).exists():
            return err('That username is already taken.', 'username')
        if User.objects.filter(email__iexact=email).exists():
            return err('An account with that email already exists.', 'email')

        user = User.objects.create_user(username=username, email=email, password=password)
        user.first_name = fullname
        user.save()
        login(request, user)

        if is_ajax:
            return JsonResponse({'success': True, 'redirect': reverse('home')})

        messages.success(request, f"Welcome to Socaily, @{username}! 🎉")
        return redirect('home')

    return render(request, 'signup.html')


# ─────────────────────────────────────────────
#  LOGIN
# ─────────────────────────────────────────────

def login_view(request):

    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':

        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        is_ajax  = _is_ajax(request)

        if not username and not password:
            error = 'Please enter your username and password.'
        elif not username:
            error = 'Please enter your username or email.'
        elif not password:
            error = 'Please enter your password.'
        else:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                if is_ajax:
                    return JsonResponse({'success': True, 'redirect': reverse('home')})
                return redirect('home')
            else:
                error = 'Sorry, your password was incorrect.'

        if is_ajax:
            return JsonResponse({'success': False, 'error': error})
        messages.error(request, error)
        return redirect('login')

    return render(request, 'login.html')


# ─────────────────────────────────────────────
#  LOGOUT
# ─────────────────────────────────────────────

def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('login')


# ─────────────────────────────────────────────
#  AVAILABILITY CHECK  (AJAX — intentionally open for signup flow)
# ─────────────────────────────────────────────

def check_availability(request):
    """GET /check-availability/?type=username&value=john"""
    check_type = request.GET.get('type', '')
    value      = request.GET.get('value', '').strip()

    if not value:
        return JsonResponse({'available': True})

    if check_type == 'username':
        exists = User.objects.filter(username__iexact=value).exists()
    elif check_type == 'email':
        exists = User.objects.filter(email__iexact=value).exists()
    else:
        return JsonResponse({'error': 'Invalid type'}, status=400)

    return JsonResponse({'available': not exists})
