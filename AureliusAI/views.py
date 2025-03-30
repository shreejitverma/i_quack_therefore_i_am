from flask import render_template

def index():
    return render_template('index.html')

def stoicism():
    return render_template('stoicism.html')

def ai():
    return render_template('AI.html')
