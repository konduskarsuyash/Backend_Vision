
import os
import re
import requests
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain_groq import ChatGroq
from datetime import datetime
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.prompts import PromptTemplate
from bs4 import BeautifulSoup  # For web scraping and HTML parsing
from langchain.text_splitter import RecursiveCharacterTextSplitter  # For splitting text into chunks
from langchain.chains.question_answering import load_qa_chain

# Initialize LLM models
jarvis_llm = ChatGroq(model='llama-3.1-70b-versatile')
supreme_llm = ChatGroq(model='llama-3.1-70b-versatile')
google_search_llm = ChatGroq(model='llama-3.1-70b-versatile')

# Memory for conversation
memory = ConversationBufferMemory()

# Function to handle user input with J.A.R.V.I.S.
def handle_user_input(user_input, memory):
    prompt = f'''
    You are J.A.R.V.I.S, a highly intelligent and informative AI assistant with a formal, yet approachable tone. Provide comprehensive and informative responses to user queries. If uncertain or need any realtime information which was not part of your training data, use "GOOOOOGLEIIIIT" followed by a concise search query. Handle "Supreme Response" queries by summarizing and formatting the information in a user-friendly manner. Reference previous conversations to tailor responses.
    
    Query:
    {user_input}

    Answer:
    '''
    # Initialize ConversationChain if not done already
    conversation = ConversationChain(memory=memory, llm=jarvis_llm)
    
    # Generate response
    response = conversation.predict(input=prompt)
    return response

# Function to invoke Supreme Model with the query
def invoke_supreme_llm(query):
    current_date = datetime.now().date()
    prompt = f"Generate a highly relevant and comprehensive Google search query for the given topic. Prioritize results with factual, up-to-date, and authoritative information. Consider using relevant keywords and phrases to optimize search results."
    messages = [
        ("system", f"Generate only one most effective Google search query to find information about the query provided to you and this is the current date {current_date} you can use this in your effective search query whenever you think you might need to use the date for generating the most effective Google search query and don't say anything else other than the most effective Google search query"),
        ("human", query),
    ]
    google_result = google_search_llm.invoke(messages)
    google_response = google_result.content.strip()
    return google_response

# Function to perform Google search and get URLs
def google_search(query, api_key, cx):
    search_url = f"https://www.googleapis.com/customsearch/v1?q={query}&num=5&key={api_key}&cx={cx}"
    try:
        response = requests.get(search_url)
        response.raise_for_status()
        search_results = response.json()
        urls = [item['link'] for item in search_results.get('items', [])]
        filtered_urls = [url for url in urls if not any(domain in url for domain in ['youtube.com', 'shiksha.com', 'tiktok.com', 'youtu.be'])]
        return filtered_urls[:5]
    except requests.exceptions.HTTPError as err:
        print(f"HTTP error occurred: {err}")
    except Exception as e:
        print(f"Error occurred: {e}")
    return []

def extract_main_content(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        text_content = soup.get_text()
        text_content = re.sub(r'\n\s*\n', '\n', text_content)
        text_content = re.sub(r'\s+', '', text_content)
        return text_content.strip()
    except requests.exceptions.HTTPError as err:
        print(f"HTTP error occurred: {err}")
    except Exception as e:
        print(f"Error occurred: {e}")
    return None

def get_text_chunks(text):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=10000, chunk_overlap=1000)
    chunks = text_splitter.split_text(text)
    return chunks

def create_embeddings(text_chunks):
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=os.getenv("GEMINI_API_KEY"))
    vector_store = FAISS.from_texts(text_chunks, embedding=embeddings)
    return vector_store

def get_supreme_model_response(user_question):
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=os.getenv("GEMINI_API_KEY"))
    new_db = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
    llm = ChatGroq(model_name="llama-3.1-70b-versatile", temperature=0.35)
    prompt_template = """
        Provide a detailed and informative answer to the question based on the given context. Ensure responses are accurate, relevant, and supported by evidence. If unable to find a definitive answer, provide potential explanations or related information. Summarize complex topics and cite sources when possible.
        \n\n
        Context:\n {context}?\n
        Question: \n{question}\n
        Answer:
    """
    chain = load_qa_chain(llm, chain_type="stuff", prompt=PromptTemplate(template=prompt_template, input_variables=["context", "question"]))
    context_value = "your_context_value"
    docs = new_db.similarity_search(user_question)
    response = chain({"input_documents": docs, "context": context_value, "question": user_question}, return_only_outputs=True)
    return response["output_text"]
