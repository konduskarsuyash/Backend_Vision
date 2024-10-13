# chat/serializers.py
from rest_framework import serializers
from .models import Chat, FileUpload,PDFDocument

class FileUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileUpload
        fields = '__all__'

class ChatSerializer(serializers.ModelSerializer):
    files = FileUploadSerializer(many=True, read_only=True)

    class Meta:
        model = Chat
        fields = ['id', 'user', 'message', 'response', 'started_at','updated_at', 'files']


class IntentSerializer(serializers.Serializer):
    message = serializers.CharField()
    

class PDFDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PDFDocument
        fields = ['pdf_file', 'question','response']