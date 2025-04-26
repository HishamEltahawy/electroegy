# you must disable DEBUG in setting to use this error handling file
from django.http import JsonResponse

def handler_404(request, exception):
    message = 'Page Not Found'
    response = JsonResponse(data={'error': message})
    response.status_code = 404
    return response

def handler_500(request):
    message = 'Error In Internal Server'
    response = JsonResponse(data={'error': message})
    response.status_code = 500
    return response