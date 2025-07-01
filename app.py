import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone

import chromadb
import markdown
from flask import Flask, render_template, request, redirect, session, flash, url_for
from markupsafe import Markup
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from openai import OpenAI, OpenAIError

from functions import get_account

# Initialize the client
ai_client = OpenAI(
    base_url=os.environ.get("AIO_BASE_URL"),
    api_key="XXX",
    default_headers={"api-key": f"{os.getenv('AIO_API_KEY')}"},
)

db_client = chromadb.PersistentClient(
    path="./private/chroma",
    settings=chromadb.config.Settings(allow_reset=True)
)

collection = db_client.get_or_create_collection("test")

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


@app.route('/')
def home():
    # Check if the user is logged in
    if 'logged_in' in session:
        return redirect(url_for('chat'))
    else:
        return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get form data
        username = request.form.get('username')
        password = request.form.get('password')

        # Check if all required fields are provided
        if not username or not password:
            flash('All fields (Username, Password) are required!')
            return render_template('login.html')

        # Hash the password with the secret key
        hashed_pass = password + app.secret_key
        hashed_pass = hashlib.sha1(hashed_pass.encode())
        password = hashed_pass.hexdigest()

        # Get the account details from the database
        account = get_account(username, password)

        # If the account exists, log the user in
        if account:
            session['logged_in'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            session['role'] = account['role']
            flash('Logged in successfully!')
            return redirect(url_for('chat'))
        else:
            flash('Combination of username and password is incorrect.')
            return render_template('login.html', hide_navbar=True)

    password = 'password'
    hashed_pass = password + app.secret_key
    hashed_pass = hashlib.sha1(hashed_pass.encode())
    password = hashed_pass.hexdigest()

    print(password)

    # Render the login template for GET requests
    return render_template('login.html', hide_navbar=True)


# Define the logout route
@app.route('/login/logout')
def logout():
    # Remove session data to log the user out
    session.pop('logged_in', None)
    session.pop('id', None)
    session.pop('username', None)

    # Redirect to login page with a success message
    flash('Logged out successfully!.')
    return redirect(url_for('login'))


# Define the chat route
@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if 'logged_in' in session:
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
                "content": "You are a general purpose assistant designed to assist Quality Assurance employees who work at iO. Keep your answers short, but accurate. In the event you are not sure about your answer, or you need additional information, please state this clearly and ask follow up questions. Also, please answer in the language the user prompts you, which is not always the same as the documentation's language. Finally, please return a response in markdown format"
            }]

            for i, msg in enumerate(chat_history):
                # Alternate between user and assistant roles
                role = "user" if i % 2 == 0 else "assistant"
                conversation.append({"role": role, "content": msg})

            try:
                # Upload files to ChromaDB
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
                    n_results=min(20, collection.count())
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

                # Create a new response with the user desired model
                if request.form.get('model') == "claude-3-7-sonnet":
                    completion = ai_client.chat.completions.create(
                        model="claude-3-7-sonnet",
                        messages=conversation,
                        temperature=1.0
                    )
                else:
                    completion = ai_client.chat.completions.create(
                        model="gpt-4o",
                        messages=conversation,
                        temperature=0.0
                    )

                chat_message = completion.choices[0].message.content

                chat_history.append(user_prompt)
                chat_history.append(chat_message)

                # Convert chat history to HTML using markdown
                chathistory_html = []
                for i, msg in enumerate(chat_history):
                    # Convert markdown to HTML
                    html_content = markdown.markdown(msg, extensions=['tables', 'fenced_code', 'codehilite'])
                    # Mark as safe for Jinja2 to render as HTML
                    chathistory_html.append(Markup(html_content))

                return render_template('home.html',
                                       chat_history=chat_history,
                                       chathistory_html=chathistory_html,
                                       context_used=context_used,
                                       model=request.form.get('model'))
            except OpenAIError as e:
                print(f"OpenAI Error: {str(e)}")
                return render_template('oi.html', error=str(e))
        else:
            # For GET requests, start with an empty conversation
            return render_template('home.html', chat_history=[], chathistory_html=[], context_used=None,
                                   model="claude-3-7-sonnet")
    else:
        return redirect(url_for('login'))


@app.errorhandler(404)
def page_not_found(e):
    return render_template('oi.html', error="404 - Niet gevonden", hide_btn=True, hide_navbar=True), 404


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
