from django.urls import path
from .views import RegisterView,LoginView,GoogleLoginApi

urlpatterns = [
    path("register/",RegisterView.as_view() ),
    path("login/",LoginView.as_view() ),
    path('login/google/', GoogleLoginApi.as_view(), name='google_login'),

]