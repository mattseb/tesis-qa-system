from django.shortcuts import render

# Create your views here.
def primero(request):
    return render(request, 'index2.html')