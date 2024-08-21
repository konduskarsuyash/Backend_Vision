

from django.contrib import admin
from django.urls import path,include
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path("admin/", admin.site.urls),
    path('account/',include('user_account.urls')),
    path('user_chats/',include('chats.urls')),
    
    path('dj-rest-auth/', include('dj_rest_auth.urls')),
    path('dj-rest-auth/registration/', include('dj_rest_auth.registration.urls')),
    path('dj-rest-auth/google/', include('allauth.socialaccount.urls')),

]+static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
