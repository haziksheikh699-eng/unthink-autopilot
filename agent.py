import os
import time
from datetime import datetime
from pathlib import Path

from google import genai
from google.genai import types

print("Starting UNTHINK AI Agent...")

# Get API key securely from GitHub Secrets
api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError(
        "GEMINI_API_KEY is missing from GitHub Secrets."
    )

client = genai.Client(api_key=api_key)

# Find available models
print("Checking available Gemini models...")

available_models = []

for model in client.models.list():
    name = model.name or ""

    actions = (
        model.supported_actions
        if hasattr(model, "supported_actions")
        else []
    ) or []

    if (
        "gemini" in name.lower()
        and "generateContent" in actions
    ):
        available_models.append(name)

print("Available generation models:", available_models)

if not available_models:
    raise RuntimeError(
        "No compatible Gemini generation models found."
    )

# Prefer lightweight Flash models
preferred_models = [
    "models/gemini-3.5-flash",
    "models/gemini-3-flash",
    "models/gemini-2.5-flash",
    "models/gemini-2.0-flash",
]

selected_model = next(
    (
        model
        for model in preferred_models
        if model in available_models
    ),
    None
)

if selected_model is None:
    flash_models = [
        model
        for model in available_models
        if "flash" in model.lower()
        and "image" not in model.lower()
        and "tts" not in model.lower()
    ]

    if not flash_models:
        raise RuntimeError(
            "No compatible Gemini Flash text model found."
        )

    selected_model = flash_models[0]

print(f"Selected model: {selected_model}")

# UNTHINK video ideas prompt
prompt = """
You are a creative YouTube strategist for UNTHINK.

UNTHINK creates stickman animation videos about:
- Psychology
- Philosophy
- Human behaviour
- Overthinking
- Relationships
- Strange everyday experiences
- Thought-provoking questions

Generate 5 original YouTube video ideas.

Requirements:
1. Make the topics interesting and clickable.
2. Avoid generic motivational content.
3. Each idea should work as a 3-6 minute animation.
4. Include a catchy title.
5. Include a short explanation.
6. Use natural, human-sounding English.
7. Avoid misleading scientific claims.
8. Suggest one simple stickman visual for each idea.

Format the response as a numbered list.
"""

# Generate ideas with retries
max_attempts = 4

for attempt in range(1, max_attempts + 1):

    try:
        print(
            f"Generating ideas: attempt "
            f"{attempt}/{max_attempts}"
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

        print("Video ideas generated successfully!")
        break

    except Exception as error:

        error_message = str(error)

        print(
            f"Attempt {attempt} failed: "
            f"{type(error).__name__}: {error_message}"
        )

        retryable = any(
            code in error_message.lower()
            for code in [
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

        wait_seconds = 15 * attempt

        print(
            f"Waiting {wait_seconds} seconds..."
        )

        time.sleep(wait_seconds)

# Save generated ideas
output_directory = Path("output")
output_directory.mkdir(exist_ok=True)

today = datetime.now().strftime("%Y-%m-%d")

output_file = output_directory / "video_ideas.md"

output_file.write_text(
    "# UNTHINK AI Video Ideas\n\n"
    f"Generated on: {today}\n\n"
    f"Model used: {selected_model}\n\n"
    f"{ideas}\n",
    encoding="utf-8",
)

print(f"Saved: {output_file}")
print("UNTHINK AI Agent completed successfully!")
