# using the Image understanding API from Gemini

import os

from dotenv import load_dotenv
from google import genai

load_dotenv()
api_key = (
    os.getenv("GEMINI_API_KEY")
 
)

if not api_key:
    raise RuntimeError(
        "Missing API key. Set GOOGLE_API_KEY, GEMINI_API_KEY, or API_KEY in your environment or .env file."
    )

client = genai.Client(api_key=api_key)

my_file = client.files.upload(file="sample2.jpg")

detailed_prompt = """You are an AI content moderation assistant. Evaluate the provided image and classify it into one of the following categories:
1. Safe Content: No explicit, violent, or harmful material. Suitable for general audiences.
2. Adult Content: Contains explicit sexual material, pornography, or graphic nudity.
3. Inappropriate Content: Contains violence, hate symbols, self-harm, illegal activities, or other policy-violating material.
Output your response with the exact classification name first, followed by a brief, objective justification for your decision."""

interaction = client.interactions.create(
    model="gemini-3.8-flash",
    input = [
    {"type": "text", "text": detailed_prompt},
    {
        "type": "image",
        "uri": my_file.uri,
        "mime_type": my_file.mime_type
    }
    ]
    
)
print(interaction.output_text)