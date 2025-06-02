
from flask import Flask, request, jsonify
import requests
import os
import json
from dotenv import load_dotenv
from flask_cors import CORS
from urllib.parse import quote

load_dotenv()

app = Flask(__name__)
CORS(app)

AZURE_SPEECH_KEY = os.environ.get("AZURE_SPEECH_KEY")
AZURE_REGION = os.environ.get("AZURE_REGION", "eastus")

@app.route("/debug", methods=["GET"])
def debug():
    test_path = "test.wav"
    if not os.path.exists(test_path):
        return jsonify({"error": "test.wav not found on server"}), 500

    with open(test_path, "rb") as f:
        audio_data = f.read()

    reference_text = "Hello, how are you?"
    assessment_params = {
        "ReferenceText": reference_text,
        "GradingSystem": "HundredMark",
        "Granularity": "Phoneme",
        "Dimension": "Comprehensive"
    }

    url = (
        f"https://{AZURE_REGION}.stt.speech.microsoft.com/speech/recognition/conversation/cognitiveservices/v1"
        f"?language=en-US"
        f"&Pronunciation-Assessment={quote(json.dumps(assessment_params))}"
    )

    headers = {
        "Ocp-Apim-Subscription-Key": AZURE_SPEECH_KEY,
        "Content-Type": "audio/wav; codecs=audio/pcm; samplerate=16000"
    }

    response = requests.post(
        url,
        headers=headers,
        data=audio_data
    )

    print("Azure debug response:", response.status_code, response.text)

    if response.status_code != 200:
        return jsonify({"error": "Azure failed", "details": response.text}), 500

    return jsonify(response.json())

if __name__ == "__main__":
    app.run(debug=True)
