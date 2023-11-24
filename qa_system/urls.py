from django.contrib import admin
from django.urls import include, path
from account import views as account
from questions import views as questions
urlpatterns = [
    path('admin/', admin.site.urls),
    path('domain/', include(('domain.urls', 'domain'), namespace='domain')),
    path('login/', include(('account.urls', 'account'), namespace='login')),
    path('questions/', include(('questions.urls', 'questions'), namespace='questions')),
    path('', account.loginPage, name='login'),
]