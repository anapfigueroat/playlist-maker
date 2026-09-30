import os 
from flask import Flask, session

app = Flask(__name__)

if __name__ == '__main__':
    app.run(debug=True)