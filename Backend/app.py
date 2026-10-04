import base64
import os
import tempfile
from pathlib import Path

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS

load_dotenv(dotenv_path=Path(__file__).with_name(".env"))

app = Flask(__name__)
allowed_origins = [
    origin.strip()
    for origin in os.getenv("FRONTEND_ORIGINS", "http://localhost:5173").split(",")
    if origin.strip()
]
CORS(app, resources={r"/*": {"origins": allowed_origins}})
MURF_API_KEY = os.getenv("MURF_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

PROMPTS = {
    "Summary": """
You are a professional tourist guide.
Provide a high-level overview of "{place}" in {language}.

Focus on:
- The historical significance
- Why the place is famous
- Key architectural or cultural highlights

Keep the explanation concise, engaging, and easy to follow.
Avoid excessive details and dates.
Limit the response to around 200 words.

Respond ONLY in {language}.
""",

    "Detailed": """
You are a professional tourist guide.
Provide a detailed and immersive explanation of "{place}" in {language}.

Cover:
- Historical background and timeline
- Architectural design and unique features
- Cultural importance and notable events
- Interesting facts and visitor insights

Explain concepts clearly and in a storytelling manner.
Include relevant details and examples to create a rich experience.
Limit the response to around 400 words.

Respond ONLY in {language}.
"""
}

def generate_speech(text, voice_id, locale):
    if not MURF_API_KEY:
        raise RuntimeError("MURF_API_KEY is not configured. Add it to Backend/.env.")

    url = "https://global.api.murf.ai/v1/speech/stream"
    headers = {
        "api-key": MURF_API_KEY,
        "Content-Type": "application/json"
    }
    data = {
    "voice_id": voice_id,
    "text": text,
    "locale": locale,
    "model": "FALCON",
    "format": "MP3",
    "sampleRate": 24000,
    "channelType": "MONO"
    }

    response = requests.post(url, headers=headers, json=data, timeout=120)
    if not response.ok:
        raise RuntimeError(
            f"Murf API returned HTTP {response.status_code}: {response.text[:500]}"
        )

    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_audio:
        temp_audio.write(response.content)
        return temp_audio.name


def generate_description(place, answer_type, language):
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is not configured. Add it to Backend/.env.")

    prompt = PROMPTS[answer_type].format(place=place, language=language)
    response = None
    for model in ("gemini-3.7-flash", "gemini-3.6-flash", "gemini-3.5-flash"):
        response = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            params={"key": GEMINI_API_KEY},
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=90,
        )
        if response.ok:
            break
        if response.status_code not in (429, 503):
            details = response.json().get("error", {}).get("message", response.text[:500])
            raise RuntimeError(f"Gemini API returned HTTP {response.status_code}: {details}")
    else:
        details = response.json().get("error", {}).get("message", response.text[:500])
        raise RuntimeError(f"Gemini models are temporarily unavailable: {details}")

    candidates = response.json().get("candidates", [])
    parts = candidates[0].get("content", {}).get("parts", []) if candidates else []
    text = "\n".join(part.get("text", "") for part in parts).strip()
    if not text:
        raise RuntimeError("Gemini returned no description. Check the model response and API access.")
    return text
    
@app.route("/generate-audio-guide", methods=["POST"])
def generate_audio_guide():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(error="Request body must be valid JSON."), 400

    required_fields = ("place", "answerType", "language", "voiceId", "locale")
    missing_fields = [field for field in required_fields if not data.get(field)]
    if missing_fields:
        return jsonify(error=f"Missing required fields: {', '.join(missing_fields)}."), 400
    if data["answerType"] not in PROMPTS:
        return jsonify(error="answerType must be Summary or Detailed."), 400

    missing_keys = [
        key_name
        for key_name, value in (
            ("GEMINI_API_KEY", GEMINI_API_KEY),
            ("MURF_API_KEY", MURF_API_KEY),
        )
        if not value
    ]
    if missing_keys:
        missing = ", ".join(missing_keys)
        if os.getenv("RENDER"):
            setup_instructions = (
                "Add the missing variables in the Render service Environment settings, "
                "then redeploy."
            )
        elif os.getenv("VERCEL"):
            setup_instructions = (
                "Add the missing variables in Vercel Project Settings > "
                "Environment Variables, then redeploy."
            )
        else:
            setup_instructions = "Add them to Backend/.env and restart the server."
        return jsonify(
            error=f"Backend configuration incomplete. Missing: {missing}. {setup_instructions}",
            missingConfiguration=missing_keys,
        ), 503

    audio_path = None
    try:
        text_description = generate_description(
            data["place"], data["answerType"], data["language"]
        )
        if not text_description:
            raise RuntimeError("Gemini returned an empty description.")

        audio_path = generate_speech(text_description, data["voiceId"], data["locale"])
        with open(audio_path, "rb") as audio_file:
            encoded_audio = base64.b64encode(audio_file.read()).decode("utf-8")

        return jsonify(description=text_description, audioBase64=encoded_audio)
    except Exception as error:
        app.logger.exception("Audio guide generation failed")
        return jsonify(error=str(error)), 502
    finally:
        if audio_path and os.path.exists(audio_path):
            os.remove(audio_path)


@app.route("/health", methods=["GET"])
def health():
    return jsonify(
        status="ok",
        configured={
            "gemini": bool(GEMINI_API_KEY),
            "murf": bool(MURF_API_KEY),
        },
    )


if __name__ == "__main__":
    app.run(debug=True)