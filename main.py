
from flask import Flask, request, jsonify
import requests
import os
import json
from dotenv import load_dotenv
from flask_cors import CORS

load_dotenv()

app = Flask(__name__)
CORS(app)

AZURE_SPEECH_KEY = os.environ.get("AZURE_SPEECH_KEY")
AZURE_REGION = os.environ.get("AZURE_REGION", "eastus")

@app.route("/assess", methods=["GET", "POST"])
def assess():
    if request.method == "GET":
        if request.args.get("debug") == "true":
            test_path = "test.wav"
            if not os.path.exists(test_path):
                return jsonify({"error": "test.wav not found on server"}), 500

            with open(test_path, "rb") as f:
                audio_data = f.read()

            reference_text = "Hello, how are you?"
        else:
            return jsonify({"error": "GET not supported without debug=true"}), 405
    else:
        if 'audio' not in request.files or 'text' not in request.form:
            return jsonify({"error": "Missing audio or reference text"}), 400

        audio_data = request.files['audio'].read()
        reference_text = request.form['text']

    headers = {
        "Ocp-Apim-Subscription-Key": AZURE_SPEECH_KEY,
        "Content-Type": "audio/wav; codecs=audio/pcm; samplerate=16000",
        "Pronunciation-Assessment": json.dumps({
            "ReferenceText": reference_text,
            "GradingSystem": "HundredMark",
            "Granularity": "Phoneme",
            "Dimension": "Comprehensive"
        })
    }

    response = requests.post(
        f"https://{AZURE_REGION}.stt.speech.microsoft.com/speech/recognition/conversation/cognitiveservices/v1?language=en-US",
        headers=headers,
        data=audio_data
    )

    print("Azure response:", response.status_code, response.text)

    if response.status_code != 200:
        return jsonify({"error": "Failed to get response from Azure", "details": response.text}), 500

    return jsonify(response.json())

@app.route("/debug", methods=["GET"])
def debug():
    test_path = "test.wav"
    if not os.path.exists(test_path):
        return jsonify({"error": "test.wav not found on server"}), 500

    with open(test_path, "rb") as f:
        audio_data = f.read()

    reference_text = "Hello, how are you?"

    headers = {
        "Ocp-Apim-Subscription-Key": AZURE_SPEECH_KEY,
        "Content-Type": "audio/wav; codecs=audio/pcm; samplerate=16000",
        "Pronunciation-Assessment": json.dumps({
            "ReferenceText": reference_text,
            "GradingSystem": "HundredMark",
            "Granularity": "Phoneme",
            "Dimension": "Comprehensive"
        })
    }

    response = requests.post(
        f"https://{AZURE_REGION}.stt.speech.microsoft.com/speech/recognition/conversation/cognitiveservices/v1?language=en-US",
        headers=headers,
        data=audio_data
    )

    print("Azure response (debug):", response.status_code, response.text)

    if response.status_code != 200:
        return jsonify({"error": "Azure failed", "details": response.text}), 500

    return jsonify(response.json())

if __name__ == "__main__":
    app.run(debug=True)
