from flask import Flask, request, jsonify
import requests
import os
import json
from dotenv import load_dotenv
from flask_cors import CORS
from urllib.parse import quote
from pydub import AudioSegment
import io

# 初始化 Flask 應用並啟用 CORS
load_dotenv()
app = Flask(__name__)
CORS(app)

# 從環境變量獲取 Azure 配置
AZURE_SPEECH_KEY = os.environ.get("AZURE_SPEECH_KEY")
AZURE_REGION = os.environ.get("AZURE_REGION", "eastus")

# 調試環境變量
print("AZURE_SPEECH_KEY:", "Set" if AZURE_SPEECH_KEY else "Not set")
print("AZURE_REGION:", AZURE_REGION)

@app.route("/debug", methods=["GET"])
def debug():
    test_path = "test.wav"
    if not os.path.exists(test_path):
        return jsonify({"error": "伺服器上未找到 test.wav"}), 500

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

    try:
        response = requests.post(url, headers=headers, data=audio_data)
        print("Azure debug 響應:", response.status_code, response.text)
        if response.status_code != 200:
            return jsonify({"error": "Azure 請求失敗", "details": response.text}), 500
        return jsonify(response.json())
    except Exception as e:
        return jsonify({"error": "伺服器錯誤", "details": str(e)}), 500

@app.route("/assess", methods=["POST"])
def assess():
    if "audio" not in request.files:
        return jsonify({"error": "未提供音頻文件"}), 400
    if "text" not in request.form:
        return jsonify({"error": "未提供參考文本"}), 400

    audio_file = request.files["audio"]
    reference_text = request.form["text"]

    audio_data = audio_file.read()
    print("Received audio size:", len(audio_data), "bytes")

    # 轉換音頻為 WAV 格式
    try:
        audio = AudioSegment.from_file(io.BytesIO(audio_data), format="webm")
        audio = audio.set_channels(1).set_frame_rate(16000).set_sample_width(2)
        output = io.BytesIO()
        audio.export(output, format="wav")
        audio_data = output.getvalue()
        print("Converted audio size:", len(audio_data), "bytes")
    except Exception as e:
        return jsonify({"error": "音頻轉換失敗", "details": str(e)}), 400

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

    try:
        response = requests.post(url, headers=headers, data=audio_data)
        print("Azure 響應:", response.status_code, response.text)
        if response.status_code != 200:
            return jsonify({"error": "Azure 請求失敗", "details": response.text}), response.status_code
        return jsonify(response.json())
    except Exception as e:
        return jsonify({"error": "伺服器錯誤", "details": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
