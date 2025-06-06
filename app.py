import json
import os
import tempfile
from datetime import datetime, timezone

import chromadb
from chromadb.utils import embedding_functions
from flask import Flask, render_template, request
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from openai import OpenAI, OpenAIError

# Initialize the client
ai_client = OpenAI(
    base_url="https://api.bonzai.iodigital.com/universal",
    api_key="XXX",
    default_headers={"api-key": f"{os.getenv('AIO_API_KEY')}"},
)

db_client = chromadb.PersistentClient(
    path="./private/chroma",
    settings=chromadb.config.Settings(allow_reset=True)
)

collection = db_client.get_or_create_collection("test")

# Defining the embedding function
embedding_func = embedding_functions.OpenAIEmbeddingFunction(
    api_base="https://api.bonzai.iodigital.com/universal",
    api_key="XXX",
    default_headers={"api-key": f"{os.getenv('AIO_API_KEY')}"},
    model_name="text-embedding-3-large"
)

# Create a Flask application instance
app = Flask(__name__,
            static_url_path='',
            static_folder='static',
            template_folder='templates')

# Disable strict slashes in URLs for Flask routing
app.url_map.strict_slashes = False

# Set the secret key for the Flask application
app.config['SECRET_KEY'] = 'hello this is qAiO'

# Add tojson filter
app.jinja_env.filters['tojson'] = json.dumps


# Define the home route
@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        # Get form data
        chat_history_str = request.form.get('chat_history', '[]')
        user_prompt = request.form.get('message')

        # Parse previous messages from JSON
        try:
            chat_history = json.loads(chat_history_str)
        except:
            chat_history = []

        # Ensure prev_message is a list
        if not isinstance(chat_history, list):
            chat_history = []

        # Prepare conversation history for the AI
        conversation = [{
            "role": "system",
            "content": "You are a general purpose assistant designed to assist Quality Assurance employees who work at iO. Keep your answers short, but accurate. In the event you are not sure about your answer, or you need additional information, please state this clearly and ask follow up questions. Also, please answer in Dutch"
        }]

        for i, msg in enumerate(chat_history):
            # Alternate between user and assistant roles
            role = "user" if i % 2 == 0 else "assistant"
            conversation.append({"role": role, "content": msg})

        try:
            # Upload files first to ChromaDB
            for file in request.files.getlist('files'):
                if file.filename != '':
                    # Create a temporary directory that works on any OS
                    temp_dir = tempfile.gettempdir()
                    temp_path = os.path.join(temp_dir, file.filename)

                    # Save file temporarily
                    file.save(temp_path)

                    pdf_loader = PyPDFLoader(temp_path)
                    text_splitter = RecursiveCharacterTextSplitter(
                        chunk_size=1000,
                        chunk_overlap=50,
                        separators=["\n\n", "\n", ". ", " ", ""],
                    )

                    documents = pdf_loader.load_and_split(text_splitter=text_splitter)

                    collection.add(
                        documents=[i.page_content for i in documents],
                        ids=[f"pdf_chunk_{i}" for i in range(len(documents))],
                        metadatas=
                        [
                            {
                                "file_name": file.filename,
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                            }
                            for _ in documents
                        ],
                    )

                    # Clean up temp file
                    os.remove(temp_path)

            # After uploading to the vector DB, search for the relevant information
            results = collection.query(
                query_texts=[user_prompt],
                n_results=4
            )

            context_used = []

            for meta in results['metadatas'][0]:
                if meta['file_name'] not in context_used:
                    context_used.append(meta['file_name'])

            # Add the new user message
            conversation.extend([
                {"role": "user", "content": f"This might be useful documentation to help the user's request:{results}"},
                {"role": "user", "content": f"This is the user's prompt:{user_prompt}"}
            ])

            # Create a new response exactly as in the documentation
            completion = ai_client.chat.completions.create(
                model="gpt-4o",
                messages=conversation,
                # temperature=0.0 # ToDo: Test different temperatures with QA'ers
            )

            chat_message = completion.choices[0].message.content

            chat_history.append(user_prompt)
            chat_history.append(chat_message)

            return render_template('home.html', chat_history=chat_history, context_used=context_used)
        except OpenAIError as e:
            print(f"OpenAI Error: {str(e)}")
            return render_template('oi.html', error=str(e))
    else:
        # For GET requests, start with an empty conversation
        return render_template('home.html', chat_history=[], context_used=None)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('oi.html', error="404 - Niet gevonden", hide_btn=True), 404


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
