from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "<h1>Hello World! Your URL Shortener project starts here.</h1>"