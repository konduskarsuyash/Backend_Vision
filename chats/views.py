from rest_framework import generics, permissions,status
from .models import Chat, FileUpload
from .serializers import ChatSerializer, FileUploadSerializer,IntentSerializer
from .generate_image import generate_image
from .imp import get_audio_input,mapintent,detect_intent
from rest_framework.response import Response
# from .scrap import handle_user_input, invoke_supreme_llm, google_search, scrape_html, save_text_as_txt, merge_text_files_to_pdf, get_pdf_text, get_text_chunks, create_vector_store, get_supreme_model_response
import os
from dotenv import load_dotenv
from langchain.memory import ConversationBufferMemory
import re
from .olama import generate_response_from_image
import base64,io
from .tp import *
from PIL import UnidentifiedImageError

from .web_search import perform_web_search
from PIL import Image
from django.conf import settings
from backend.settings import BASE_DIR
load_dotenv()


gpi_cx=os.getenv('GOOGLE_CUSTOM_SEARCH_ENGINE_ID')

#for image generation
class ChatListCreateView(generics.ListCreateAPIView):
    serializer_class = ChatSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Chat.objects.filter(user=self.request.user)

    def post(self, request, *args, **kwargs):
        u_input = request.data.get('transcript')
        print("******* ChatListCrateView",u_input)
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


#web search 
class ChatbotView(generics.GenericAPIView):
    serializer_class = ChatSerializer

    def post(self, request, *args, **kwargs):
        print("******** Full Request Data:", request.data)

        user_input = request.data.get('transcript')
        print("******** ChatBotView",user_input)

        # Detect the intent from the user input
        intent = detect_intent(user_input)
        print(f"Detected intent in backend: {intent.content}")
        if intent:
            print(f"Intent detected: {intent.content}")
        else:
            print("Intent detection failed.")
            return Response({"error": "Could not detect intent."}, status=status.HTTP_400_BAD_REQUEST)
            
        print(f"Detected intent: {intent.content}")

        # Determine which function to run based on the detected intent
        action_result = mapintent(intent.content, user_input)
        print(f"Action result: {action_result}")

        if intent.content == '2':  # Image generation
            return Response({"image_filename": action_result}, status=status.HTTP_200_OK)
        elif intent.content == '4':  # Real-time web search
            response = handle_user_input(user_input)
            print("user_input response: " ,response)

            
            if "GOOOOOGLEIIIIT" in response:

                search_suggestion = re.search(
                    r'GOOOOOGLEIIIIT\s*([^.]+)', response)
                if search_suggestion:
                    supreme_query = search_suggestion.group(1).strip()
                    google_query = invoke_supreme_llm(supreme_query)
                    api_key = os.getenv("GOOGLE_SEARCH_API_KEY")
                    cx = os.getenv("GOOGLE_CUSTOM_SEARCH_ENGINE_ID")
                    google_urls = google_search(google_query, api_key=api_key, cx=cx)

                    print("********google urls",google_urls)
                    process_urls(google_urls)

                    supreme_response = get_supreme_model_response(user_input)

                    jarvis_response = handle_user_input(supreme_response)

                
                    return Response({"response": supreme_response}, status=status.HTTP_200_OK)
            return Response({"response": response}, status=status.HTTP_200_OK)

        # Handle other intents similarly
        # elif intent.content == 'X':
        #     return Response({"result": action_result}, status=status.HTTP_200_OK)

        return Response({"error": "Could not process the request."}, status=status.HTTP_400_BAD_REQUEST)

def capture_image(image_data):
    try:
        # Decode base64 image data
        image_data = base64.b64decode(image_data)
      
        # Convert the byte stream to an image   
        return image_data
    except Exception as e:
        raise Exception(f"Failed to decode image data: {e}")
    
    

class CaptureImageView(generics.GenericAPIView):
    serializer_class = ChatSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        image_file = request.FILES.get('image_data')  # Accessing the uploaded file
        question = request.data.get('question')

        print("***CaptureImage view", question)
        print("Received image file:", image_file)

        intent = detect_intent(question)
        print(f"Detected intent in backend: {intent.content}")
        if intent:
            print(f"Intent detected: {intent.content}")
        else:
            print("Intent detection failed.")
            return Response({"error": "Could not detect intent."}, status=status.HTTP_400_BAD_REQUEST)

        if not image_file or image_file.size == 0:
            return Response({"error": "Image file not provided or is empty."}, status=status.HTTP_400_BAD_REQUEST)

        print("Entering in try-except block")

        try:
            # Convert InMemoryUploadedFile to bytes
            image_bytes = image_file.read()  # Convert the image to raw bytes
            print(f"Image bytes length: {len(image_bytes)}")  # Debugging output for byte length

            # Check if the image bytes are non-zero
            if len(image_bytes) == 0:
                raise ValueError("Empty image file received.")

            # Open the image with PIL
            image = Image.open(io.BytesIO(image_bytes))  # Now the image is correctly opened
            print(f"Image format: {image.format}")  # Log the format of the image

            # Create media directory if it doesn't exist
            media_directory = os.path.join(BASE_DIR, 'media')  # Ensure BASE_DIR is defined
            if not os.path.exists(media_directory):
                os.makedirs(media_directory)
            print("Creating media directory")

            # Save the image to a file
            image_path = os.path.join(media_directory, 'captured_image.jpg')
            image.save(image_path)  # Now that the image is loaded, it can be saved
            print(f"Image saved to {image_path}")

            # Now base64 encode the image for API calls
            buffered = io.BytesIO()
            image.save(buffered, format="JPEG")
            encoded_image = base64.b64encode(buffered.getvalue()).decode('utf-8')

        except UnidentifiedImageError:
            return Response({"error": "Cannot identify image file."}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            print("Error decoding")
            print(f"Error while processing the image: {str(e)}")  # Debugging output
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # Proceed with image processing and response generation
        response = generate_response_from_image(encoded_image, question)

        # Create the chat object
        chat = Chat.objects.create(
            user=request.user,
            message=question,
            response=response
        )

        # Create a FileUpload object
        FileUpload.objects.create(
            chat=chat,
            file=image_path,
            file_type='image'
        )

        return Response({"response": response, "image_path": image_path}, status=status.HTTP_200_OK)



class IntentDetectionView(generics.GenericAPIView):
    serializer_class = IntentSerializer

    def post(self, request, *args, **kwargs):
        # Retrieve the user message from the request
        user_message = request.data.get('message')

        if not user_message:
            return Response({"error": "Message not provided"}, status=status.HTTP_400_BAD_REQUEST)

        # Detect intent from the user input
        intent = detect_intent(user_message)
        if not intent:
            return Response({"error": "Could not detect intent."}, status=status.HTTP_400_BAD_REQUEST)

        # Attempt to extract and validate the intent number
        try:
            intent_value = intent.content.strip()  
            intent_number = int(intent_value)  
            print(intent_number)
        except (ValueError, AttributeError) as e:
            # If there's an error in conversion or accessing intent.content, log and respond with error
            print(f"Error parsing intent: {e}")
            return Response({"error": "Invalid intent format."}, status=status.HTTP_400_BAD_REQUEST)

        # Log and return the detected intent number
        print(f"Detected intent number: {intent_number}")
        return Response({"intent_number": intent_number}, status=status.HTTP_200_OK)
