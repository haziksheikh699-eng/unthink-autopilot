
from datetime import datetime
from pathlib import Path

print("Starting UNTHINK AI Agent...")

topics = [
    "Why intelligent people overthink everything",
    "The psychology of being alone",
    "Why we remember embarrassing moments",
    "Why time feels faster as we grow older",
    "The hidden psychology of overthinking"
]

Path("output").mkdir(exist_ok=True)

today = datetime.now().strftime("%Y-%m-%d")

with open("output/video_ideas.md", "w", encoding="utf-8") as file:
    file.write("# UNTHINK Video Ideas\n\n")
    file.write(f"Generated on: {today}\n\n")

    for i, topic in enumerate(topics, 1):
        file.write(f"{i}. {topic}\n")
        print(f"Topic {i}: {topic}")

print("UNTHINK Agent completed successfully!")
