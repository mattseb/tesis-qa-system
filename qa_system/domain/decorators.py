from django.http import HttpResponse
from django.shortcuts import redirect

def unauthenticated_user(view_function):
    def wrapper_function(request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('home')
        else:
            return view_function(request, *args, **kwargs)
    return wrapper_function

def allowed_users(allowed_roles=[]):
    def decorator(view_function):
        def wrapper_func(request, *args, **kwargs):
            print("Funciona", allowed_roles)
            group = None
            print(request.user.groups)
            if request.user.groups.exists():
                group = request.user.groups.all()[0].name

                if group in allowed_roles:
                    return view_function(request, *args, **kwargs)
                else:
                    return HttpResponse('Permisos insuficientes')
            else:
                print("kue")
        return wrapper_func
    return decorator