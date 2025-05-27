from flask import Flask, render_template, request
from openai import OpenAI, OpenAIError
import json, os, tempfile

# Initialize OpenAI client
client = OpenAI(
    api_key=os.getenv('OPENAI_API_KEY'),
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
        message = request.form.get('message')

        # Parse previous messages from JSON
        try:
            chat_history = json.loads(chat_history_str)
        except:
            chat_history = []

        # Ensure prev_message is a list
        if not isinstance(chat_history, list):
            chat_history = []

        # Prepare conversation history for the AI
        conversation = []
        for i, msg in enumerate(chat_history):
            # Alternate between user and assistant roles
            role = "user" if i % 2 == 0 else "assistant"
            conversation.append({"role": role, "content": msg})

        try:
            # Upload files first
            file_ids = []
            file_names = []

            for file in request.files.getlist('files'):
                if file.filename != '':
                    # Create a temporary directory that works on any OS
                    temp_dir = tempfile.gettempdir()
                    temp_path = os.path.join(temp_dir, file.filename)

                    # Save file temporarily
                    file.save(temp_path)

                    # Debug information
                    print(f"Uploading file: {file.filename}")

                    # Upload using the exact same method as the documentation
                    with open(temp_path, "rb") as f:
                        uploaded_file = client.files.create(
                            file=f,
                            purpose="user_data"
                        )

                    # Clean up temp file
                    os.remove(temp_path)

                    file_ids.append(uploaded_file.id)
                    file_names.append(file.filename)

            # Build content for the API request exactly as in the documentation
            user_content = []

            # Add file references
            for file_id in file_ids:
                user_content.append({
                    "type": "input_file",
                    "file_id": file_id,
                })

            # Add the text message
            user_content.append({
                "type": "input_text",
                "text": message,
            })

            # Add the new user message
            conversation.append({"role": "user", "content": user_content})

            # Create a new response exactly as in the documentation
            response = client.responses.create(
                model="gpt-4.1",
                instructions="You are a general purpose assistant designed to assist scouts leaders from the scouts club called: Scouting Johan en Cornelis de Witt-MeDo. Keep your answers short, but accurate. In the event you are not sure about your answer, please state this clearly and ask follow up questions. Also please answer in Dutch",
                input=conversation,
                store=False,
                # temperature=0.0 # ToDo: Test different temperatures with QA'ers
            )

            chat_history.append(user_content)
            chat_history.append(response.output_text)

            return render_template('home.html', chat_history=chat_history)
        except OpenAIError as e:
            print(f"OpenAI Error: {str(e)}")
            return render_template('oi.html', error=str(e))
    else:
        # For GET requests, start with an empty conversation
        return render_template('home.html', chat_history=[])


@app.errorhandler(404)
def page_not_found(e):
    return render_template('oi.html', error="404 - Niet gevonden", hide_btn=True), 404


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)