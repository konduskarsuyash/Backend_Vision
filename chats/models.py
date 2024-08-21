# chat/models.py
from django.contrib.auth.models import User
from django.db import models

class Chat(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chats')
    message = models.TextField()
    response = models.TextField()
    started_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Chat by {self.user.username} at {self.started_at}"

class FileUpload(models.Model):
    FILE_TYPE_CHOICES = (
        ('image', 'Image'),
        ('document', 'Document'),
    )

    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='files')
    file = models.FileField(upload_to='uploads/')
    file_type = models.CharField(max_length=50, choices=FILE_TYPE_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_file_type_display()} {self.file.name} for Chat {self.chat.id}"
