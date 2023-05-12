from flask import Flask
from flashcards.routes import flashcards


def create_app():
    app = Flask(__name__)
    app.register_blueprint(flashcards)
    return app


app = create_app()
app.run(debug=True, port="8000")
