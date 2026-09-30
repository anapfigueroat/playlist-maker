import os 
from dotenv import load_dotenv
from flask import Flask

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(64)

CLIENT_ID = os.environ.get("CLIENT_ID")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")

if __name__ == '__main__':
    app.run(debug=True)