import os
import shutil
import time
from PIL import Image
from gtts import gTTS
from playsound import playsound
import speech_recognition as sr
from gradio_client import Client
from langchain import PromptTemplate
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from backend.settings import BASE_DIR
from django.conf import settings
load_dotenv()


# Initialize Gradio and LangChain clients
client = Client("stabilityai/stable-diffusion-3-medium")
groq_api_key = os.getenv('GROQ_API_KEY')
llm = ChatGroq(model='llama-3.1-70b-versatile', api_key=groq_api_key)

# Define the prompt template for intent detection
template = """
You are an AI capable of detecting the intent of a message. 
Based on the message provided, return the corresponding number I dont need anything else just return the number so that i can use it in a function:
1 If u would need Vision capablity (i.e if u would need access of camera),
2 for image generation,
3 for RAG (Retrieval-Augmented Generation) (i.e if u need to take input of a document of access users database),
4 for real-time web search ( U would need to look at latest info from internet).
5 Normal conversation doesnt need anything.

Message: {message}
"""

# Create the PromptTemplate objec
def generate_image(query):
    try:
        result = client.predict(
            prompt=query,
            negative_prompt="",
            seed=0,
            randomize_seed=True,
            width=1024,
            height=1024,
            guidance_scale=5,
            num_inference_steps=28,
            api_name="/infer"
        )
        temp_image_path = result[0]
        media_filename = 'generated_image.png'
        media_path = os.path.join(settings.MEDIA_ROOT, media_filename)
        os.makedirs(os.path.dirname(media_path), exist_ok=True)
        shutil.copy(temp_image_path, media_path)
        print(f"Image saved to {media_path}")
        return media_filename  # Return filename only
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

