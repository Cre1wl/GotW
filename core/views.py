from django.shortcuts import render

def home(request):
    """Главная страница с описанием функционала"""
    return render(request, 'core/home.html')