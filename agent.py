import os
import time
from datetime import datetime
from pathlib import Path

from google import genai
from google.genai import types

print("Starting UNTHINK AI Agent...", flush=True)

# Read API key securely from GitHub Secrets
api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError(
        "GEMINI_API_KEY is missing from GitHub Secrets."
    )

# Connect to Gemini
client = genai.Client(api_key=api_key)

print("Connected to Gemini API.", flush=True)

# Discover available Gemini Flash models
print("Checking available Gemini models...", flush=True)

available_models = []

for model in client.models.list():
    name = model.name or ""

    if (
        "gemini" in name.lower()
        and "flash" in name.lower()
        and "image" not in name.lower()
        and "tts" not in name.lower()
        and "embedding" not in name.lower()
    ):
        available_models.append(name)

print("Available Flash models:", available_models, flush=True)

if not available_models:
    raise RuntimeError(
        "No Gemini Flash models were found for this API key."
    )

# Prefer newer Flash models
preferred_models = [
    "models/gemini-3.8-flash",
    "models/gemini-3.5-flash",
    "models/gemini-3-flash",
    "models/gemini-2.5-flash",
]

selected_model = next(
    (
        name
        for name in preferred_models
        if name in available_models
    ),
    available_models[0]
)

print(f"Selected model: {selected_model}", flush=True)

# Prompt for UNTHINK
prompt = """
You are an expert YouTube strategist for UNTHINK.

UNTHINK creates stickman animation videos exploring:
- Psychology
- Philosophy
- Human behaviour
- Overthinking
- Relationships
- Strange everyday experiences
- Thought-provoking questions

Generate 5 original YouTube video ideas.

Requirements:
1. Create interesting, clickable titles.
2. Avoid generic motivational content.
3. Make each topic suitable for a 3-6 minute video.
4. Include a short explanation for each idea.
5. Include one simple stickman animation concept per idea.
6. Use natural, human-sounding English.
7. Avoid misleading scientific claims.
8. Make the topics varied and thought-provoking.

Format the response as a numbered list.
"""

# Generate ideas with automatic retries
max_attempts = 5
ideas = None

for attempt in range(1, max_attempts + 1):
    try:
        print(
            f"Generating ideas: attempt {attempt}/{max_attempts}",
            flush=True
        )

        response = client.models.generate_content(
            model=selected_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.9,
                max_output_tokens=2500,
            ),
        )

        ideas = response.text

        if not ideas or not ideas.strip():
            raise RuntimeError(
                "Gemini returned an empty response."
            )

        print("AI ideas generated successfully!", flush=True)
        break

    except Exception as error:
        error_message = str(error).lower()

        print(
            f"Attempt {attempt} failed: "
            f"{type(error).__name__}: {error}",
            flush=True
        )

        retryable = any(
            word in error_message
            for word in [
                "503",
                "unavailable",
                "overloaded",
                "500",
                "502",
                "504",
                "429",
                "resource_exhausted",
            ]
        )

        if not retryable or attempt == max_attempts:
            raise

        wait_seconds = min(15 * attempt, 60)

        print(
            f"Waiting {wait_seconds} seconds before retry...",
            flush=True
        )

        time.sleep(wait_seconds)

# Create output folder
output_directory = Path("output")
output_directory.mkdir(exist_ok=True)

# Prepare output file
today = datetime.now().strftime("%Y-%m-%d")
output_file = output_directory / "video_ideas.md"

# Save generated ideas
output_file.write_text(
    "# UNTHINK AI Video Ideas\n\n"
    f"Generated on: {today}\n\n"
    f"Model used: {selected_model}\n\n"
    f"{ideas}\n",
    encoding="utf-8"
)

print(f"Saved generated ideas to: {output_file}", flush=True)
print("UNTHINK AI Agent completed successfully!", flush=True)
