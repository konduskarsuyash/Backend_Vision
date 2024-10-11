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
def check_file_type(file_path):
    # Get the file extension
    _, file_extension = os.path.splitext(file_path)

    # Determine the type based on the file extension
    if file_extension.lower() == ".pdf":
        return "PDF"
    elif file_extension.lower() in [".jpeg", ".jpg", ".png", ".gif"]:
        return "Image"
    elif file_extension.lower() == ".doc":
        return "Word Document"
    elif file_extension.lower() == ".docx":
        return "Word Document (.docx)"
    else:
        return "Unknown file type"