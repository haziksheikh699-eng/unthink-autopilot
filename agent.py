
import json
import os
import time
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

print("Starting UNTHINK AI Agent...")

# Read Gemini API key from GitHub Secrets
api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError("GEMINI_API_KEY is missing.")

# Instructions for Gemini
prompt = """
You are a creative YouTube strategist for UNTHINK.

UNTHINK is a YouTube channel creating stickman animation
videos about psychology, philosophy, human behaviour,
overthinking, emotions, relationships, and unusual ideas.

Generate 5 original and engaging YouTube video ideas.

Requirements:
1. Make the topics interesting and clickable.
2. Avoid generic motivational content.
3. Focus on psychology, philosophy and human behaviour.
4. Make each idea suitable for a 3-6 minute animation.
5. Use natural, human-sounding English.
6. Include a catchy title and a short explanation.
7. Avoid misleading scientific claims.
8. Make the ideas visually interesting for stickman animation.

Format the response as a numbered list.
"""

# Gemini API endpoint
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

# Automatically retry temporary API failures
max_attempts = 5

for attempt in range(1, max_attempts + 1):
    try:
        print(
            f"Contacting Gemini: attempt "
            f"{attempt}/{max_attempts}"
        )

        with urlopen(request, timeout=60) as response:
            result = json.load(response)

        print("Gemini responded successfully!")
        break

    except HTTPError as error:
        details = error.read().decode(
            "utf-8", errors="replace"
        )

        if (
            error.code in (429, 500, 502, 503, 504)
            and attempt < max_attempts
        ):
            wait_seconds = min(
                10 * (2 ** (attempt - 1)), 80
            )

            print(
                f"Gemini returned HTTP {error.code}. "
                f"Retrying in {wait_seconds} seconds..."
            )

            time.sleep(wait_seconds)
            continue

        raise RuntimeError(
            f"Gemini API returned HTTP {error.code}: "
            f"{details}"
        ) from None

    except URLError as error:
        if attempt < max_attempts:
            print(
                "Connection problem. "
                "Retrying in 10 seconds..."
            )
            time.sleep(10)
            continue

        raise RuntimeError(
            f"Could not connect to Gemini: {error.reason}"
        ) from None

# Extract Gemini's response
try:
    parts = result["candidates"][0]["content"]["parts"]
    ideas = "\n".join(
        part["text"]
        for part in parts
        if "text" in part
    )

    if not ideas.strip():
        raise ValueError("Empty response")

except (KeyError, IndexError, TypeError, ValueError):
    raise RuntimeError(
        "Gemini did not return usable text."
    ) from None

# Create output directory
Path("output").mkdir(exist_ok=True)

today = datetime.now().strftime("%Y-%m-%d")

# Save AI-generated ideas
output_file = Path("output/video_ideas.md")

output_file.write_text(
    f"# UNTHINK AI Video Ideas\n\n"
    f"Generated on: {today}\n\n"
    f"{ideas}\n",
    encoding="utf-8"
)

print("UNTHINK AI Agent completed successfully!")
print(f"Generated ideas saved to: {output_file}")
