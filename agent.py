
import os
import time
import random
from datetime import datetime, timezone
from pathlib import Path

import httpx
from google import genai
from google.genai import types

print("Starting UNTHINK Production Agent...", flush=True)

# Read the private key from GitHub Secrets
api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError("GEMINI_API_KEY is missing.")

client = genai.Client(
    api_key=api_key,
    http_options=types.HttpOptions(timeout=120000)
)

# Retry temporary server and connection problems
retryable_errors = (
    httpx.RemoteProtocolError,
    httpx.ConnectError,
    httpx.ReadError,
    httpx.ReadTimeout,
    httpx.ConnectTimeout,
)

def retry_call(action, description, attempts=5):
    for attempt in range(1, attempts + 1):
        try:
            print(
                f"{description}: attempt {attempt}/{attempts}",
                flush=True
            )
            return action()

        except Exception as error:
            message = str(error).lower()
            status = getattr(error, "code", None)

            temporary = (
                isinstance(error, retryable_errors)
                or status in (429, 500, 502, 503, 504)
                or any(
                    term in message
                    for term in (
                        "503",
                        "overloaded",
                        "unavailable",
                        "resource_exhausted",
                        "server disconnected",
                    )
                )
            )

            if not temporary or attempt == attempts:
                raise

            wait = min(10 * (2 ** (attempt - 1)), 60)
            wait += random.uniform(0, 3)

            print(
                f"Temporary error: {type(error).__name__}. "
                f"Retrying in {wait:.1f} seconds.",
                flush=True
            )
            time.sleep(wait)

# Find available Gemini Flash models
def list_flash_models():
    names = []

    for model in client.models.list():
        name = model.name or ""
        lower = name.lower()

        if (
            "gemini" in lower
            and "flash" in lower
            and "image" not in lower
            and "tts" not in lower
            and "embedding" not in lower
            and "live" not in lower
        ):
            names.append(name)

    return names

available_models = retry_call(
    list_flash_models,
    "Discovering Gemini models"
)

if not available_models:
    raise RuntimeError("No Gemini Flash models were found.")

# Optional: set GEMINI_MODEL to a model that worked before
requested_model = os.environ.get("GEMINI_MODEL", "").strip()

preferred_models = [
    "models/gemini-3.8-flash",
    "models/gemini-3.5-flash",
    "models/gemini-3-flash",
    "models/gemini-2.5-flash",
]

if requested_model:
    selected_model = requested_model
else:
    selected_model = next(
        (
            name for name in preferred_models
            if name in available_models
        ),
        available_models[0]
    )

print(f"Using model: {selected_model}", flush=True)

# Consistent animation character design
character_style = """
A minimalist 2D stickman with a round white head,
thick black outlines, expressive black eyes,
thin black arms and legs, and simple facial expressions.
Clean off-white background, restrained red accents,
soft cinematic shadows, 16:9 widescreen composition.
The same character design must appear in every scene.
"""

# Main production prompt
prompt = f"""
You are the creative director, writer, storyboard artist,
and YouTube strategist for the channel UNTHINK.

UNTHINK explores:
- Psychology and philosophy
- Human behaviour and emotions
- Relationships and loneliness
- Strange everyday experiences
- Uncomfortable truths and thought-provoking questions

YOUR TASK:
Automatically choose ONE strong video topic and develop
a complete, practical stickman-animation production package.

TOPIC SELECTION:
First brainstorm 5 distinctive possible topics internally.
Select the one with the strongest curiosity hook,
storytelling potential, originality, and visual possibilities.

Do not claim you have checked live YouTube trends.
Avoid repeating generic motivational advice.
Prefer a specific, surprising question or observation.

OUTPUT IN MARKDOWN WITH THESE EXACT SECTIONS:

# UNTHINK VIDEO PRODUCTION PACKAGE

## 1. Selected Topic
Give the chosen topic, its central question,
why viewers might find it interesting,
and its core psychological or philosophical insight.

## 2. Video Strategy
Give the target audience, emotional tone,
viewer curiosity hook, and estimated runtime.
Choose a natural runtime, approximately 3-5 minutes.

## 3. Complete Voiceover Script
Write a complete, original, conversational English
voiceover script of approximately 450-650 words.

Requirements:
- Open with a compelling hook.
- Use short, natural sentences.
- Sound human, not like generic AI motivation.
- Develop the idea with relatable examples.
- Keep a subtle cinematic storytelling tone.
- Explain psychological claims carefully.
- End with a memorable thought or question.
- No unnecessary introductions or requests to subscribe.
- The script must be ready to record.

## 4. Six-Scene Storyboard
Create EXACTLY SIX numbered scenes.

For each scene provide:
- Scene number and short name
- Approximate duration in seconds
- Exact voiceover passage assigned to this scene
- Visual description
- Stickman actions and facial expressions
- Props and background
- Camera framing and movement
- On-screen text, only if useful
- Editing transition and sound design suggestion

Assign the entire voiceover to the six scenes in order.
Do not omit script passages or invent new narration.
Make durations consistent with the estimated runtime.

## 5. Character Consistency Guide
Use this visual design throughout:

{character_style}

Explain how to keep the character consistent
across every generated image and animation.

## 6. Six Image Generation Prompts
Provide one detailed, standalone image prompt
for each of the six scenes.

Each prompt must:
- Repeat the consistent character description
- Describe the correct setting, action and expression
- Specify 16:9 landscape framing
- Use a clean minimalist cinematic style
- Avoid unnecessary text in the generated image
- Maintain consistent props and character identity

## 7. Six Image-to-Video Prompts
Provide one animation prompt for each scene.

Each must specify:
- Character motion and expression changes
- Camera movement
- Environmental movement if needed
- Approximate clip duration
- Stable character proportions
- No morphing, flickering or random new objects

If the scene needs longer than a short animation clip,
explain how to use cuts or repeatable shots.

## 8. Thumbnail Package
Provide:
- One high-click-potential thumbnail concept
- A short text overlay of at most four words
- Facial expression and composition
- Background and accent colours
- A complete thumbnail image-generation prompt

The thumbnail should complement, not duplicate,
the title. Avoid misleading clickbait.

## 9. YouTube SEO Package
Provide:
- Three compelling title options
- One recommended title
- A natural YouTube description
- Five relevant hashtags
- Ten relevant search tags
- A pinned-comment question

Do not invent search-volume statistics.

## 10. CapCut Editing Guide
Give a practical mobile-friendly editing sequence,
music mood, sound effects, transitions,
captions guidance, and 1080p export suggestions.

## 11. Production Checklist
Give a practical checklist for turning this
package into a finished YouTube video.

QUALITY RULES:
- Use clear English.
- Be specific and visually creative.
- Avoid generic AI-style motivational writing.
- Do not fabricate scientific studies or citations.
- Keep the production achievable for a small creator.
- Do not say images or videos have been generated.
- Deliver the complete package, not just an outline.
"""

# Request the full production package
def generate_package():
    response = client.models.generate_content(
        model=selected_model,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.8,
            max_output_tokens=12000,
        ),
    )

    if not response.text or not response.text.strip():
        raise RuntimeError(
            "Gemini returned an empty production package."
        )

    return response.text

package = retry_call(
    generate_package,
    "Generating complete UNTHINK production package"
)

# Save the results
output_dir = Path("output")
output_dir.mkdir(exist_ok=True)

date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

package_file = output_dir / "unthink_production_package.md"

package_file.write_text(
    f"<!-- Generated: {date}; Model: {selected_model} -->\n\n"
    + package.strip()
    + "\n",
    encoding="utf-8",
)

# Also save a small run information file
info_file = output_dir / "generation_info.txt"

info_file.write_text(
    f"Channel: UNTHINK\n"
    f"Generated: {date} UTC\n"
    f"Model: {selected_model}\n"
    f"Output: unthink_production_package.md\n",
    encoding="utf-8",
)

print(f"Saved: {package_file}", flush=True)
print(f"Saved: {info_file}", flush=True)
print("UNTHINK production package completed!", flush=True)

client.close()
