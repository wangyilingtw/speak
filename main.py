from flask import Flask, request, jsonify, render_template
import requests
import os
import json
from dotenv import load_dotenv
from flask_cors import CORS
from urllib.parse import quote
from pydub import AudioSegment
import io

load_dotenv()
app = Flask(__name__)
CORS(app)

AZURE_SPEECH_KEY = os.environ.get("AZURE_SPEECH_KEY")
AZURE_REGION = os.environ.get("AZURE_REGION", "eastus")

@app.route("/assess", methods=["POST"])
def assess():
    if "audio" not in request.files:
        return jsonify({"error": "未提供音頻文件"}), 400
    if "text" not in request.form:
        return jsonify({"error": "未提供參考文本"}), 400

    audio_file = request.files["audio"]
    reference_text = request.form["text"]

    audio_data = audio_file.read()
    if len(audio_data) == 0:
        return jsonify({"error": "音頻數據為空"}), 400

    try:
        # 轉換 WebM → WAV (16kHz, mono, PCM 16-bit)
        audio = AudioSegment.from_file(io.BytesIO(audio_data), format="webm")
        audio = audio.strip_silence(silence_thresh=-35, silence_len=300)
        audio = audio.set_channels(1).set_frame_rate(16000).set_sample_width(2)

        # Debug 音訊格式
        print("📢 Converted audio format:")
        print(" - Channels:", audio.channels)
        print(" - Frame rate:", audio.frame_rate)
        print(" - Sample width (bytes):", audio.sample_width)

        output = io.BytesIO()
        audio.export(output, format="wav")
        audio_data = output.getvalue()

        print("🟦 Converted audio size (bytes):", len(audio_data))
    except Exception as e:
        return jsonify({"error": "音頻轉換失敗", "details": str(e)}), 400

    assessment_params = {
        "ReferenceText": reference_text,
        "GradingSystem": "HundredMark",
        "Granularity": "Phoneme",
        "Dimension": "Comprehensive",
        "EnableMiscue": True,
        "PhonemeAlphabet": "IPA"
    }

    url = (
        f"https://{AZURE_REGION}.stt.speech.microsoft.com/speech/recognition/conversation/cognitiveservices/v1"
        f"?language=en-US&format=detailed"
        f"&PronunciationAssessment={quote(json.dumps(assessment_params))}"
    )

    print("🌐 Final request URL:", url)

    headers = {
        "Ocp-Apim-Subscription-Key": AZURE_SPEECH_KEY,
        "Content-Type": "audio/wav; codecs=audio/pcm; samplerate=16000",
        "Accept": "application/json"
    }

    try:
        response = requests.post(url, headers=headers, data=audio_data)

        # Debug Azure 回應
        print("🟨 Azure status code:", response.status_code)
        print("🟨 Azure response text:", response.text)

        if response.status_code != 200:
            return jsonify({"error": "Azure 請求失敗", "details": response.text}), response.status_code
        return jsonify(response.json())
    except Exception as e:
        return jsonify({"error": "伺服器錯誤", "details": str(e)}), 500

@app.route("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
