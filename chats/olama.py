import base64
import io
from PIL import Image
import cv2
import ollama
from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv('GROQ_API_KEY'))

def capture_image():
    # Capture image using OpenCV
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    cap.release()

    # Convert the frame to base64
    _, buffer = cv2.imencode('.jpg', frame)
    image_data = base64.b64encode(buffer).decode('utf-8')

    # Decode base64 image data to PIL Image
    image = Image.open(io.BytesIO(base64.b64decode(image_data)))
    return image

def generate_response_from_image(image, question):
    # Save the captured image
    image_path = 'temp_image.jpg'
    image.save(image_path)

    # Generate text using the LLaVA model
    context = ollama.generate(
        model='llava',
        prompt=question,
        images=[image_path],
        stream=False
    )['response']

    # Send the context and question to Groq
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "You are a friendly AI Voice assistant that will be given a question and context of what's visible from the camera."
            },
            {
                "role": "user",
                "content": f"Based on context: {context} and question: {question}, reply to me like my male best friend"
            }
        ],
        model="llama3-8b-8192"
    )

    result = chat_completion.choices[0].message.content
    return result
