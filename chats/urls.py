from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from .views import ChatListCreateView, FileUploadViewSet, ChatbotView,CaptureImageView,IntentDetectionView

urlpatterns = [
    path('chat/', ChatListCreateView.as_view(), name='chat-list-create'),
    path('upload/', FileUploadViewSet.as_view(), name='file-upload-list-create'),
    path('scrap/', ChatbotView.as_view(), name='chatbot'),
    path('capture-image/', CaptureImageView.as_view(), name='capture-image'),
    path('detect_intent/', IntentDetectionView.as_view(), name='detect_intent'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)