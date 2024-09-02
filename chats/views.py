from rest_framework import generics, permissions,status
from .models import Chat, FileUpload
from .serializers import ChatSerializer, FileUploadSerializer
from .generate_image import generate_image
from .imp import get_audio_input,mapintent,detect_intent
from rest_framework.response import Response
# from .scrap import handle_user_input, invoke_supreme_llm, google_search, scrape_html, save_text_as_txt, merge_text_files_to_pdf, get_pdf_text, get_text_chunks, create_vector_store, get_supreme_model_response
import os
from dotenv import load_dotenv
from langchain.memory import ConversationBufferMemory
import re
from .olama import generate_response_from_image,capture_image
import base64,io
from .tp import handle_user_input, invoke_supreme_llm, google_search, extract_main_content, get_text_chunks, create_embeddings, get_supreme_model_response

from .web_search import perform_web_search
from PIL import Image
from django.conf import settings

load_dotenv()

class ChatListCreateView(generics.ListCreateAPIView):
    serializer_class = ChatSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Chat.objects.filter(user=self.request.user)

    def post(self, request, *args, **kwargs):
        u_input = request.data.get('transcript')
        if u_input is None:
            return Response({"error": "Transcript data is missing or invalid."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            intent = detect_intent(u_input)
            image_filename = mapintent(intent.content, u_input)
            
            # Create the chat object first
            chat = Chat.objects.create(
                user=request.user,
                message=u_input,
            )
            
            # Initialize image_path
            image_path = None
            
            if image_filename:
                # Store only the filename in the database
                FileUpload.objects.create(
                    chat=chat,
                    file=image_filename,  # Store only the filename
                    file_type='image'
                )
                # Construct the full URL for the response
                image_path = f"{settings.MEDIA_URL}{image_filename}"

            serializer = self.get_serializer(chat)
            return Response({"chat": serializer.data, "image_path": image_path}, status=status.HTTP_201_CREATED)
        except Exception as e:
            print(f"Error in post method: {e}")
            return Response({"error": "An error occurred while processing the request."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




class FileUploadViewSet(generics.ListCreateAPIView):
    queryset = FileUpload.objects.all()
    serializer_class = FileUploadSerializer
    permission_classes = [permissions.IsAuthenticated]



class ChatbotView(generics.GenericAPIView):
    serializer_class = ChatSerializer

    def post(self, request, *args, **kwargs):
        user_input = request.data.get('message')

        # Detect the intent from the user input
        intent = detect_intent(user_input)
        if intent:
            print(f"Intent detected: {intent.content}")
        else:
            print("Intent detection failed.")
            return Response({"error": "Could not detect intent."}, status=status.HTTP_400_BAD_REQUEST)
            
        print(f"Detected intent: {intent.content}")

        # Determine which function to run based on the detected intent
        action_result = mapintent(intent.content, user_input)

        if intent.content == '2':  # Image generation
            return Response({"image_filename": action_result}, status=status.HTTP_200_OK)
        elif intent.content == '4':  # Real-time web search
            search_result = perform_web_search(user_input)
            return Response({"response": search_result}, status=status.HTTP_200_OK)

        # Handle other intents similarly
        # elif intent.content == 'X':
        #     return Response({"result": action_result}, status=status.HTTP_200_OK)

        return Response({"error": "Could not process the request."}, status=status.HTTP_400_BAD_REQUEST)

def capture_image(image_data):
    try:
        # Decode base64 image data
        image_data = base64.b64decode(image_data)
        image = Image.open(io.BytesIO(image_data))
        return image
    except Exception as e:
        raise Exception(f"Failed to decode image data: {e}")
    
    

class CaptureImageView(generics.GenericAPIView):
    serializer_class = ChatSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        image_data = request.data.get('image_data')
        question = request.data.get('question')
        
        print(question)

        if not image_data or not question:
            return Response({"error": "Image or question not provided."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            image = capture_image(image_data)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # Proceed with image processing and response generation
        response = generate_response_from_image(image, question)

        # Create the chat object
        chat = Chat.objects.create(
            user=request.user,
            message=question,
            response=response
        )

        image_path = os.path.join('media', 'captured_image.jpg')
        image.save(image_path)

        # Save the image to the correct path
        image.save(image_path)

        # Create a FileUpload object
        FileUpload.objects.create(
            chat=chat,
            file=image_path,
            file_type='image'
        )

        return Response({"response": response, "image_path": image_path}, status=status.HTTP_200_OK)
