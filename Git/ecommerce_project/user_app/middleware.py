from typing import Any
from django.shortcuts import redirect
from django.urls import reverse
from django.shortcuts import render

class RedirectAuthenticatedUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    
    def __call__(self, request):
        if not request.user.is_authenticated:
            return self.get_response(request)
        
        if request.path.startswith('/accounts/'):
            return redirect(reverse('index_page'))
        
        return self.get_response(request)


class CustomExceptionHandlerMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        return render(request, 'error_page.html', {'error_message': 'An error occurred during processing. Please try again later.'}, status=500)