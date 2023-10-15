from googletrans import Translator
import functions_framework


@functions_framework.http
def translate_http(request):
    request_json = request.get_json(silent=True)
    request_args = request.args

    print("request_json:", request_json)
    print("request_args:", request_args)

    translator = Translator()

    text = "Welcome to AC215"
    src = "en"
    dest = "es"
    if request_args and "text" in request_args:
        text = request_args["text"]
    if request_args and "src" in request_args:
        src = request_args["src"]
    if request_args and "dest" in request_args:
        dest = request_args["dest"]

    results = translator.translate(text, src=src, dest=dest)
    print("Output:", results.text)

    return results.text
