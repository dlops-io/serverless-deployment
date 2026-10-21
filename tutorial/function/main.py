"""Part 1: deploy these two files using Cloud Run's function editor."""

import functions_framework
from googletrans import Translator


@functions_framework.http
def hello_http(request):
    text = request.args.get("text", "Welcome to AC215")
    source = request.args.get("src", "en")
    destination = request.args.get("dest", "es")
    return Translator().translate(text, src=source, dest=destination).text
