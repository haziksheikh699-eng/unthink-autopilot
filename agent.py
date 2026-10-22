
import json
import os
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

print("Starting UNTHINK AI Agent...")

api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError("GEMINI_API_KEY is missing.")

prompt = """
You are a creative YouTube strategist for UNTHINK.

UNTHINK makes engaging stickman animation videos about:
- Psychology
- Philosophy
- Human behaviour
- Strange everyday experiences
- Thought-provoking questions

Generate 5 original YouTube video ideas.

Requirements:
- Interesting and clickable, without misleading claims
- Suitable for 3-6 minute stickman animations
- Simple enough to illustrate
- Avoid generic motivational topics
- Mix psychology and philosophy
- For each idea, include a title and a short explanation
- Use natural, human-sounding English
"""

url = (
    "https://generativelanguage.googleapis.com/v1beta/"
    "models/gemini-3.5-flash:generateContent"
)

payload = {
    "contents": [
        {
            "parts": [
                {"text": prompt}
            ]
        }
    ],
    "generationConfig": {
        "temperature": 0.9,
        "maxOutputTokens": 1800
    }
}

request = Request(
    url,
    data=json.dumps(payload).encode("utf-8"),
    headers={
        "Content-Type": "application/json",
        "x-goog-api-key": api_key
    },
    method="POST"
)

try:
    with urlopen(request, timeout=60) as response:
        result = json.load(response)
except HTTPError as error:
    details = error.read().decode("utf-8", errors="replace")
    raise RuntimeError(
        f"Gemini API returned HTTP {error.code}: {details}"
    ) from None
except URLError as error:
    raise RuntimeError(
        f"Could not connect to Gemini: {error.reason}"
    ) from None

try:
    ideas = result["candidates"][0]["content"]["parts"][0]["text"]
except (KeyError, IndexError, TypeError):
    raise RuntimeError(
        "Gemini did not return usable text."
    ) from None

Path("output").mkdir(exist_ok=True)

today = datetime.now().strftime("%Y-%m-%d")

output_file = Path("output/video_ideas.md")

output_file.write_text(
    f"# UNTHINK AI Video Ideas\n\n"
    f"Generated on: {today}\n\n"
    f"{ideas}\n",
    encoding="utf-8"
)

print("Gemini generated video ideas successfully!")
print(f"Saved to: {output_file}")
