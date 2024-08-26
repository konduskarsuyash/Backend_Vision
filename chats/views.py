from rest_framework import generics, permissions,status
from .models import Chat, FileUpload
from .serializers import ChatSerializer, FileUploadSerializer
from .generate_image import generate_image
from .imp import get_audio_input,mapintent,detect_intent
from rest_framework.response import Response
from .scrap import handle_user_input, invoke_supreme_llm, google_search, scrape_html, save_text_as_txt, merge_text_files_to_pdf, get_pdf_text, get_text_chunks, create_vector_store, get_supreme_model_response
import os
from dotenv import load_dotenv
import re
from .olama import generate_response_from_image,capture_image
import base64,io
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

        def get_queryset(self):
            return Chat.objects.filter(user=self.request.user)

        def post(self, request, *args, **kwargs):
            user_input = get_audio_input()  # Capture the audio input and convert it to text

            if user_input:
                # Save the chat with the converted text
                chat = Chat.objects.create(
                    user=self.request.user,
                    message=user_input  # Store the converted text
                )

                # Process the input through J.A.R.V.I.S.
                response = handle_user_input(user_input)
                

                if "GOOOOOGLEIIIIT" in response:
                    # Extract the search suggestion
                    search_suggestion = re.search(r'GOOOOOGLEIIIIT\s*([^\.]+)', response)
                    if search_suggestion:
                        supreme_query = search_suggestion.group(1).strip()

                        # Call the supreme model to refine the query
                        google_query = invoke_supreme_llm(supreme_query)
                        print("****google query***",google_query)

                        # Perform Google search using the refined query
                        api_key = os.getenv("GOOGLE_SEARCH_API_KEY")
                        cx = os.getenv("GOOGLE_CUSTOM_SEARCH_ENGINE_ID")
                        urls = google_search(google_query, api_key, cx)
                        
                        if not urls:
                            return Response({"response": "Google Search did not return any relevant results."}, status=status.HTTP_200_OK)


                        if urls:
                            contents = []
                            for url in urls:
                                content = scrape_html(url)
                                print(f"Content from {url}: {content[:500]}...")  # Log the first 500 characters

                                if content:
                                    contents.append(content)

                            # Save scraped content as text files
                            text_filenames = []
                            for i, content in enumerate(contents):
                                filename = f"scraped_text_{i+1}.txt"
                                save_text_as_txt(content, filename)
                                text_filenames.append(filename)

                            # Merge text files into a PDF
                            merge_text_files_to_pdf(text_filenames, "combined_content.pdf")

                            # Extract text from the combined PDF
                            pdf_text = get_pdf_text(["combined_content.pdf"])

                            if pdf_text:
                                # Break down the PDF text into chunks and store in vector embeddings
                                text_chunks = get_text_chunks(pdf_text)
                                create_vector_store(text_chunks)

                            # Call the supreme model again to generate the final response
                            supreme_response = get_supreme_model_response(user_input)
                            response = supreme_response
                        else:
                            response = "Could not retrieve useful information from Google Search."

                # Update the chat instance with the response
                    print("Final Response:", response)
                    chat.response = response
                    chat.save()


                return Response({"response": response}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Audio input could not be processed."}, status=status.HTTP_400_BAD_REQUEST)


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
