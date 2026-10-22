import os
import time
import random
from datetime import datetime
from pathlib import Path

import httpx
from google import genai
from google.genai import types


# ==========================================
# UNTHINK AUTOPILOT
# AI VIDEO IDEA GENERATOR
# ==========================================

print("Starting UNTHINK Autopilot...", flush=True)

API_KEY = os.environ.get("GEMINI_API_KEY")

if not API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY is missing. "
        "Add it to GitHub repository secrets."
    )

client = genai.Client(
    api_key=API_KEY,
    http_options=types.HttpOptions(
        timeout=60000
    )
)


# ==========================================
# RETRY SYSTEM
# ==========================================

RETRYABLE_HTTP_CODES = {
    429, 500, 502, 503, 504
}

RETRYABLE_CONNECTION_ERRORS = (
    httpx.RemoteProtocolError,
    httpx.ConnectError,
    httpx.ReadError,
    httpx.ReadTimeout,
    httpx.ConnectTimeout,
)


def is_retryable(error):
    code = getattr(error, "code", None)

    try:
        if int(code) in RETRYABLE_HTTP_CODES:
            return True
    except (TypeError, ValueError):
        pass

    if isinstance(error, RETRYABLE_CONNECTION_ERRORS):
        return True

    message = str(error).lower()

    return any(
        text in message
        for text in (
            "server disconnected",
            "connection reset",
            "temporarily unavailable",
            "overloaded",
            "remoteprotocolerror",
        )
    )


def retry_call(function, description, attempts=3):

    for attempt in range(1, attempts + 1):

        try:
            print(
                f"{description}: "
                f"attempt {attempt}/{attempts}",
                flush=True
            )

            return function()

        except Exception as error:

            print(
                f"Error: {type(error).__name__}: "
                f"{error}",
                flush=True
            )

            if not is_retryable(error):
                raise

            if attempt == attempts:
                raise

            delay = min(
                10 * (2 ** (attempt - 1)),
                40
            ) + random.uniform(0, 3)

            print(
                f"Retrying in {delay:.1f} seconds...",
                flush=True
            )

            time.sleep(delay)


# ==========================================
# DISCOVER GEMINI MODELS
# ==========================================

def discover_models():

    models = []

    for model in client.models.list():

        name = model.name or ""

        lower_name = name.lower()

        if "gemini" not in lower_name:
            continue

        if "flash" not in lower_name:
            continue

        if any(
            excluded in lower_name
            for excluded in (
                "image",
                "tts",
                "embedding",
                "live",
                "audio",
            )
        ):
            continue

        models.append(name)

    return models


available_models = retry_call(
    discover_models,
    "Discovering Gemini models"
)

print(
    "Available Gemini Flash models:",
    available_models,
    flush=True
)

if not available_models:
    raise RuntimeError(
        "No Gemini Flash models were returned "
        "for this API key."
    )


# ==========================================
# MODEL PRIORITY
# ==========================================

preferred_models = [
    "models/gemini-3.8-flash",
    "models/gemini-3.5-flash",
    "models/gemini-3-flash",
    "models/gemini-2.5-flash",
]

ordered_models = []

for name in preferred_models:
    if name in available_models:
        ordered_models.append(name)

for name in available_models:
    if name not in ordered_models:
        ordered_models.append(name)

print(
    "Model candidates:",
    ordered_models,
    flush=True
)


# ==========================================
# UNTHINK CONTENT PROMPT
# ==========================================

PROMPT = """
You are the creative director of UNTHINK,
a YouTube channel that makes stickman animations.

The channel explores:

- Psychology
- Philosophy
- Human behaviour
- Strange everyday experiences
- Overthinking
- Emotions
- Relationships
- Uncomfortable truths
- Thought-provoking questions

Generate FIVE original YouTube video ideas.

REQUIREMENTS:

1. Create interesting, clickable titles.
2. Avoid generic motivational topics.
3. Use natural, human-sounding English.
4. Make each idea suitable for a 3-6 minute video.
5. Include a short explanation for each topic.
6. Suggest one stickman animation concept.
7. Avoid misleading scientific claims.
8. Make the ideas varied and distinctive.

OUTPUT FORMAT:

IDEA 1
Title:
Explanation:
Stickman visual:

IDEA 2
Title:
Explanation:
Stickman visual:

Continue until IDEA 5.
"""


# ==========================================
# GENERATE VIDEO IDEAS
# ==========================================

def generate_with_model(model_name):

    response = client.models.generate_content(
        model=model_name,
        contents=PROMPT,
        config=types.GenerateContentConfig(
            temperature=0.9,
            max_output_tokens=2500
        )
    )

    if not response.text:
        raise RuntimeError(
            "Gemini returned an empty response."
        )

    return response.text


ideas = None
selected_model = None
last_error = None

for model_name in ordered_models:

    print(
        f"Trying model: {model_name}",
        flush=True
    )

    try:
        ideas = retry_call(
            lambda: generate_with_model(model_name),
            f"Generating ideas with {model_name}",
            attempts=3
        )

        selected_model = model_name
        break

    except Exception as error:

        last_error = error

        code = getattr(error, "code", None)

        # Stop on authentication and permission errors.
        if str(code) in ("401", "403"):
            raise

        # Stop on quota errors to avoid bypassing
        # project-level usage limits.
        if str(code) == "429":
            raise

        # Try another model for unavailable models
        # or temporary service failures.
        if str(code) in ("404", "500", "502", "503", "504"):
            print(
                "Trying another available model...",
                flush=True
            )
            continue

        if isinstance(
            error,
            RETRYABLE_CONNECTION_ERRORS
        ):
            print(
                "Connection failed. Trying next model...",
                flush=True
            )
            continue

        raise


if not ideas:
    raise RuntimeError(
        "All compatible model attempts failed. "
        f"Last error: {last_error}"
    )


# ==========================================
# SAVE RESULTS
# ==========================================

output_dir = Path("output")
output_dir.mkdir(exist_ok=True)

today = datetime.now().strftime("%Y-%m-%d")

output_file = output_dir / "video_ideas.md"

output_file.write_text(
    "# UNTHINK AI Video Ideas\n\n"
    f"Generated on: {today}\n\n"
    f"Model: {selected_model}\n\n"
    f"{ideas}\n",
    encoding="utf-8"
)

print(
    f"SUCCESS! Saved: {output_file}",
    flush=True
)

client.close()

print(
    "UNTHINK Autopilot completed successfully!",
    flush=True
)
