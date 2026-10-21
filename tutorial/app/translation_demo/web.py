"""Part 2 UI; part 3 speech route remains explicitly unimplemented."""

from flask import Flask, jsonify, render_template, request

from .speech import synthesize
from .translation import LANGUAGES, translate, validate


def create_app():
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = 32 * 1024

    @app.get("/")
    def index():
        return render_template("index.html", languages=LANGUAGES)

    def inputs():
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            raise ValueError("Send a JSON object.")
        text = data.get("text", "")
        source = data.get("src", "en")
        destination = data.get("dest", "fr")
        validate(text, source, destination)
        return text, source, destination

    @app.post("/api/translate")
    def translation():
        try:
            text, source, destination = inputs()
        except ValueError as exc:
            return jsonify(error=str(exc)), 400
        try:
            result = translate(text, source, destination)
        except Exception:
            app.logger.exception("External translation request failed")
            return jsonify(error="The translation provider could not complete the request."), 502
        return jsonify(text=result, src=source, dest=destination)

    @app.post("/api/speech")
    def speech():
        try:
            text, _, language = inputs()
        except ValueError as exc:
            return jsonify(error=str(exc)), 400
        try:
            audio, mime_type = synthesize(text, language)
        except NotImplementedError as exc:
            return jsonify(error=str(exc)), 501
        return app.response_class(audio, mimetype=mime_type)

    return app
