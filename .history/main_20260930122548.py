import os 
from flask import Flask

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(64)

CLIENT_ID = "4baec0cbea5a455c868df836c5ca2abf"
CLIENT_SECRET = "ef611cf1ec0f4dd0ae9e37e09b8156c5"

if __name__ == '__main__':
    app.run(debug=True)