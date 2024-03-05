from django.shortcuts import render


def index_page(request):
    return render(request, 'index.html')


def sign_in(request):
    return render(request, 'login.html')