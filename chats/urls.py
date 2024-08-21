from django.urls import path
from .views import ChatListCreateView, FileUploadViewSet, ChatbotView,CaptureImageView

urlpatterns = [
    path('chat/', ChatListCreateView.as_view(), name='chat-list-create'),
    path('upload/', FileUploadViewSet.as_view(), name='file-upload-list-create'),
    path('scrap/', ChatbotView.as_view(), name='chatbot'),
    path('capture-image/', CaptureImageView.as_view(), name='capture-image'),
]
