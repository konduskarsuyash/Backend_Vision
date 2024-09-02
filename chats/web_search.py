import os
from .tp import invoke_supreme_llm, google_search, extract_main_content, get_text_chunks, create_embeddings, get_supreme_model_response

def perform_web_search(query):
    print(query)
    try:
        # Generate a Google search query using the supreme LLM
        google_query = invoke_supreme_llm(query)
        print("Generated Google search query:", google_query)
        api_key = os.getenv("GOOGLE_SEARCH_API_KEY")
        cx = os.getenv("GOOGLE_CUSTOM_SEARCH_ENGINE_ID")

        # Perform the Google search and get URLs
        urls = google_search(google_query, api_key, cx)
        print(f"API Key: {api_key}, CX: {cx}")
        print("URLs found:", urls)

        if urls:
            all_text_chunks = []
            for url in urls:
                content = extract_main_content(url)
                if content:
                    all_text_chunks.extend(get_text_chunks(content))

            if all_text_chunks:
                # Create and save embeddings from the web search content
                vector_store = create_embeddings(all_text_chunks)
                vector_store.save_local("faiss_index")

                # Generate a supreme model response based on the user query and search results
                supreme_response = get_supreme_model_response(query)
                return supreme_response

        return "No relevant information could be found."
    except Exception as e:
        print(f"An error occurred during web search: {e}")
        return "An error occurred while performing the web search."
