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

@app.route("/assess", methods=["POST"])
def assess():
    # Debug 模式：提供內建測試音訊和文字
    if request.args.get("debug") == "true":
        reference_text = "Hello, how are you?"
        with open("test.wav", "rb") as f:
            audio_data = f.read()
        print("🔍 Debug mode: using internal test.wav and sentence.")
    else:
        if 'audio' not in request.files or 'text' not in request.form:
            return jsonify({"error": "Missing audio or reference text"}), 400

        audio_file = request.files['audio']
        reference_text = request.form['text']
        audio_file.stream.seek(0)
        audio_data = audio_file.read()

    # 建立 header
    headers = {
        "Ocp-Apim-Subscription-Key": AZURE_SPEECH_KEY,
        "Content-Type": "audio/wav; codecs=audio/pcm; samplerate=16000",
        "Accept": "application/json",
        "Pronunciation-Assessment": json.dumps({
            "ReferenceText": reference_text,
            "GradingSystem": "HundredMark",
            "Granularity": "Phoneme",
            "Dimension": "Comprehensive"
        })
    }

    print("📤 Sending request to Azure with headers:")
    print(json.dumps(headers, indent=2))

    response = requests.post(
        f"https://{AZURE_REGION}.stt.speech.microsoft.com/speech/recognition/conversation/cognitiveservices/v1?language=en-US",
        headers=headers,
        data=audio_data
    )

    print(f"📥 Azure returned status {response.status_code}")
    print("📝 Azure raw response:", response.text[:500])  # 前500字

    if response.status_code != 200:
        return jsonify({
            "error": "Failed to get response from Azure",
            "details": response.text
        }), 500

    return jsonify(response.json())

if __name__ == "__main__":
    app.run(debug=True)


