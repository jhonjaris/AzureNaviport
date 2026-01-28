from django.shortcuts import render
from django.contrib.auth.decorators import login_required

# Create your views here.

@login_required
def dashboard(request):
    # Vista placeholder para reportes
    return render(request, 'dashboard_placeholder.html', {
        'title': 'Reportes',
        'user': request.user
    })
