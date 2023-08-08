from django.contrib import admin
from django.urls import include, path
from account import views
urlpatterns = [
    path('admin/', admin.site.urls),
    path('domain/', include(('domain.urls', 'domain'), namespace='domain')),
    path('login/', include(('account.urls', 'account'), namespace='login')),
    path('', views.loginPage, name='login'),
]