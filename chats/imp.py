from langchain import PromptTemplate
from langchain_groq import ChatGroq
import speech_recognition as sr
import os 
from dotenv import load_dotenv
# from .olama import generate_response_from_camera
from .olama import generate_response_from_image
from .generate_image import generate_image
# from rag import check_file_type , generate_image_response
from .tp import handle_user_input
from .web_search import perform_web_search

load_dotenv()

groq_api_key = os.getenv('GROQ_API_KEY')

llm = ChatGroq(model='llama-3.1-70b-versatile')

template = """
You are an AI capable of detecting the intent of a message. 
Based on the message provided, return the corresponding number I dont need anything else just return the number so that i can use it in a function:
1 If u would need Vision capablity (i.e if u would need access of camera) u would need this when a user asks for eg what i am currrently holding or what i am doing etc ,
2 for image generation,
3 for RAG (Retrieval-Augmented Generation) (i.e if u need to take input of a document of access users database) if user asks to upload image,take input of document or image ,etc,
4 for real-time web search ( U would need to look at latest info from internet).
5 Normal conversation doesnt need anything.

Message: {message}
"""
# Create the PromptTemplate object
prompt_template = PromptTemplate(
    input_variables=["message"],
    template=template,
)

# Define a function to detect intent
def detect_intent(user_message):
    print(user_message)
    prompt = prompt_template.format(message=user_message)
    response = llm.invoke(prompt)
    return response

def mapintent(intent,query):
    if intent == '1':
        print(generate_response_from_image(query))
    elif intent == '2':
        print('calling generation of image')
        image_filename = generate_image(query) 
        return image_filename
    elif intent == '3':
        print('calling pdf part')
        uploads_dir = "uploads"

# # Iterate over all files in the directory
#         for filename in os.listdir(uploads_dir):
#           file_path = os.path.join(uploads_dir, filename)
#           if os.path.isfile(file_path): 
#             file_type = check_file_type(file_path)
#             print(f"{filename}: {file_type}")
#             if file_type=="Image":
#                 print(generate_image_response(file_path,query))
    elif intent == '4':
        print('Performing real-time web search')
        web_search_result = perform_web_search(query)
        return web_search_result
#     elif intent=='5':
#         return 'Chat-bot'
#     elif intent=='6':
#         return 'Databse Context required'
def get_audio_input(user_input):
    # recognizer = sr.Recognizer()
    # with sr.Microphone() as source:
    #     print("Please say something...")
    #     audio = recognizer.listen(source)

    #     try:
    #         # Recognize speech using Google Web Speech API
    #         user_input = recognizer.recognize_google(audio)
    #         print(f"You said: {user_input}")
    #         return user_input
    #     except sr.UnknownValueError:
    #         print("Sorry, I could not understand the audio.")
    #         return None
    #     except sr.RequestError as e:
    #         print(f"Could not request results from Google Web Speech API; {e}")
    # You can process the input here if needed
    print(f"User input: {user_input}")
    return user_input


# Example usage
# user_message = get_audio_input()
# intent = detect_intent(user_message)
# # print(intent)
# result=mapintent(intent.content,user_message)
# print(result)