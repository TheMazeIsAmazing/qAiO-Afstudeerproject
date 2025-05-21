from flask import Flask, render_template, request
from openai import OpenAI
import json, os

client = OpenAI(
    base_url=os.getenv('AIO_BASE_URL'),
    api_key="XXX",
    default_headers={"api-key": f"{os.getenv('AIO_API_KEY')}"},
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
        prev_message_str = request.form.get('prev_message', '[]')
        message = request.form.get('message')

        # Parse previous messages from JSON
        try:
            prev_message = json.loads(prev_message_str)
        except:
            prev_message = []

        # Ensure prev_message is a list
        if not isinstance(prev_message, list):
            prev_message = []

        # Prepare conversation history for the AI
        conversation = []
        for i, msg in enumerate(prev_message):
            # Alternate between user and assistant roles
            role = "user" if i % 2 == 0 else "assistant"
            conversation.append({"role": role, "content": msg})

        # Add the new user message
        conversation.append({"role": "user", "content": message})

        print(f"conversation: {conversation}")

        # Call the API with the full conversation history
        completion = client.chat.completions.create(
            model="claude-3-7-sonnet",
            messages=conversation,
            # temperature=0.0 # ToDo: Test different temperatures with QA'ers
        )

        chat_message = completion.choices[0].message.content

        # Update message history
        prev_message.append(message)
        prev_message.append(chat_message)

        # print(f"User message: {message}")
        # print(f"AI response: {chat_message}")
        # print(f"Message history: {prev_message}")
        print(f"conversation: {conversation}")


        return render_template('home.html', chat_messages=prev_message)
    else:
        return render_template('home.html', chat_messages=[])


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)