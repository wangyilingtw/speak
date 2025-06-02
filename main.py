from flask import Flask, request, jsonify
import requests
import os
import json
from dotenv import load_dotenv
from flask_cors import CORS

load_dotenv()

app = Flask(__name__)
CORS(app)  # 允許跨網域請求

AZURE_SPEECH_KEY = os.environ.get("AZURE_SPEECH_KEY")
AZURE_REGION = os.environ.get("AZURE_REGION", "eastus")

@app.route("/assess", methods=["POST"])
def assess():
    if 'audio' not in request.files or 'text' not in request.form:
        return jsonify({"error": "Missing audio or reference text"}), 400

    audio_file = request.files['audio']
    reference_text = request.form['text']

    # 避免 InvalidHeader 錯誤：使用 json.dumps 建立單行 JSON 字串
    assessment_config = json.dumps({
        "ReferenceText": reference_text,
        "GradingSystem": "HundredMark",
        "Granularity": "Phoneme",
        "Dimension": "Comprehensive"
    })

    headers = {
        "Ocp-Apim-Subscription-Key": AZURE_SPEECH_KEY,
        "Content-Type": "audio/wav; codecs=audio/pcm; samplerate=16000",
        "Pronunciation-Assessment": assessment_config
    }

    response = requests.post(
        f"https://{AZURE_REGION}.stt.speech.microsoft.com/speech/recognition/conversation/cognitiveservices/v1?language=en-US",
        headers=headers,
        data=audio_file.read()
    )

    if response.status_code != 200:
        return jsonify({"error": "Failed to get response from Azure", "details": response.text}), 500

    return jsonify(response.json())

if __name__ == "__main__":
    app.run(debug=True)
