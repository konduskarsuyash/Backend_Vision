import os
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext, load_index_from_storage
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set OpenAI API key from environment variable
openai_api_key = os.getenv('OPENAI_API_KEY')
if openai_api_key:
    os.environ["OPENAI_API_KEY"] = openai_api_key
else:
    raise ValueError("No OpenAI API key found. Please set the OPENAI_API_KEY environment variable.")

# Directory to store PDFs
PERSIST_DIR = "./storage"

def setup_index(data_directory="data"):
    """
    Set up the VectorStoreIndex with documents in the data directory.
    """
    if not os.path.exists(PERSIST_DIR):
        # Load the documents and create the index
        documents = SimpleDirectoryReader(data_directory).load_data()
        index = VectorStoreIndex.from_documents(documents, show_progress=True)
        # Persist the index for future queries
        index.storage_context.persist(persist_dir=PERSIST_DIR)
    else:
        # Load the existing index from storage
        storage_context = StorageContext.from_defaults(persist_dir=PERSIST_DIR)
        index = load_index_from_storage(storage_context)
    
    return index
def query_index(query, data_directory="data"):
    """
    Query the LlamaIndex with a given query and return the response.
    """
    # Set up the index
    index = setup_index(data_directory)

    # Set up the query engine
    query_engine = index.as_query_engine()

    # Query the index
    response = query_engine.query(query)

    # Check the response and return a string or dictionary
    if hasattr(response, 'content'):
        return response.content  # or extract any specific attribute you need

    # If the response is just text
    return str(response)  # Convert to string if it's not already


def handle_pdf_and_question(pdf_path, question):
    """
    Handles the document upload and question using LlamaIndex.
    This function processes the document and answers the question.
    """
    # Assuming the document is already moved to 'data' directory
    print(f"Processing document: {pdf_path}")
    response = query_index(question)
    return response

# Sample usage: Uncomment to use
# response = query_index("What is the limitation?")
# print(response)
