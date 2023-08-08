from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('domain/', include(('domain.urls', 'domain'), namespace='domain')),
    path('login/', include(('account.urls', 'account'), namespace='login')),
]