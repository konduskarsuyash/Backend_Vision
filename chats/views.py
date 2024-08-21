from rest_framework import generics, permissions,status
from .models import Chat, FileUpload
from .serializers import ChatSerializer, FileUploadSerializer
from .generate_image import get_audio_input,generate_image
from rest_framework.response import Response
from .scrap import handle_user_input, invoke_supreme_llm, google_search, scrape_html, save_text_as_txt, merge_text_files_to_pdf, get_pdf_text, get_text_chunks, create_vector_store, get_supreme_model_response
import os
from dotenv import load_dotenv
import re
from .olama import capture_image, generate_response_from_image

load_dotenv()


class ChatListCreateView(generics.ListCreateAPIView):
    serializer_class = ChatSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Chat.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Capture and convert audio input
        user_message = get_audio_input()
        if user_message:
            # Save the chat with the converted text
            chat = serializer.save(
                user=self.request.user,
                message=user_message  # Store the converted text
            )
            # Generate an image or any other response if needed
            image_path = generate_image(user_message)  # Assuming you have a generate_image function
            if image_path:
                FileUpload.objects.create(
                    chat=chat,
                    file=image_path,
                    file_type='image'
                )
            return chat
        else:
            return None

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


class CaptureImageView(generics.GenericAPIView):
    serializer_class = ChatSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        # Capture the image
        image = capture_image()

        # Get the question from the request data
        question = get_audio_input()

        if image and question:
            # Generate a response based on the image and question
            response = generate_response_from_image(image, question)

            # Create the chat object
            chat = Chat.objects.create(
                user=request.user,
                message=question,
                response=response
            )

            # Define the correct image path
            image_filename = f"user_{request.user.id}_captured_image.jpg"
            image_path = os.path.join('uploads', image_filename)

            # Ensure the directory exists
            os.makedirs(os.path.dirname(image_path), exist_ok=True)

            # Save the image to the correct path
            image.save(image_path)

            # Create a FileUpload object
            FileUpload.objects.create(
                chat=chat,
                file=image_filename,
                file_type='image'
            )

            return Response({"response": response}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Failed to capture image or question not provided."}, status=status.HTTP_400_BAD_REQUEST)