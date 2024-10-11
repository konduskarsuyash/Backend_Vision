from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv('GROQ_API_KEY'))


def generate_response_from_image(image, question):
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "What's in this image?"},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image}",
                        },
                    },
                ],
            }
        ],
        model="llama-3.2-11b-vision-preview",
        
    )
    image_context = chat_completion.choices[0].message.content

    # Send the context and question to Groq
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "You are a friendly AI Voice assistant that will be given a question and context of what's visible from the camera."
            },
            {
                "role": "user",
                "content": f"Based on context: {image_context} and question: {question}, reply to me like my male best friend"
            }
        ],
        model="llama3-8b-8192"
    )

    result = chat_completion.choices[0].message.content
    return result
