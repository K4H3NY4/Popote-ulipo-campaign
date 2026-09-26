import os
import base64

from dotenv import load_dotenv
from google import genai

# --------------------------------------------------
# Configuration
# --------------------------------------------------
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError("Missing GEMINI_API_KEY in your environment or .env file.")

client = genai.Client(api_key=api_key)

FOREGROUND_IMAGE = "sample2.jpg"
BACKGROUND_IMAGE = "background_image.jpg"
OUTPUT_IMAGE = "fashion_ecommerce_shot.png"


# --------------------------------------------------
# Step 1: Moderate / classify the uploaded selfie
# --------------------------------------------------
def moderate_image(image_path: str) -> str:
    uploaded_file = client.files.upload(file=image_path)

    moderation_prompt = """You are an AI content moderation assistant. Evaluate the provided image and classify it into one of the following categories:
1. Safe Content: No explicit, violent, or harmful material. Suitable for general audiences.
2. Adult Content: Contains explicit sexual material, pornography, or graphic nudity.
3. Inappropriate Content: Contains violence, hate symbols, self-harm, illegal activities, or other policy-violating material.
Output your response with the exact classification name first, followed by a brief, objective justification for your decision."""

    interaction = client.interactions.create(
        model="gemini-3.8-flash",
        input=[
            {"type": "text", "text": moderation_prompt},
            {
                "type": "image",
                "uri": uploaded_file.uri,
                "mime_type": uploaded_file.mime_type,
            },
        ],
    )

    return interaction.output_text


# --------------------------------------------------
# Step 2: Merge foreground image with background
# --------------------------------------------------
def merge_images(
    foreground_path: str,
    background_path: str,
    output_path: str,
) -> None:
    with open(foreground_path, "rb") as f:
        foreground_bytes = f.read()

    with open(background_path, "rb") as f:
        background_bytes = f.read()

    merge_prompt = """Create a professional mosaic image where the background image is slightly faded and the foreground image is clearly visible. Make the foreground image look like a styled sticker without changing the person/image itself. The background should remain faded, with the foreground centered and starting from the bottom of the background image. Create a polished composite of the two images."""

    interaction = client.interactions.create(
        model="gemini-3.1-flash-image",
        input=[
            {
                "type": "image",
                "data": base64.b64encode(foreground_bytes).decode("utf-8"),
                "mime_type": "image/jpeg",
            },
            {
                "type": "image",
                "data": base64.b64encode(background_bytes).decode("utf-8"),
                "mime_type": "image/jpeg",
            },
            {"type": "text", "text": merge_prompt},
        ],
    )

    for step in interaction.steps:
        if step.type != "model_output":
            continue

        for content_block in step.content:
            if content_block.type == "text":
                print(content_block.text)
            elif content_block.type == "image":
                with open(output_path, "wb") as f:
                    f.write(base64.b64decode(content_block.data))
                print(f"Merged image saved to: {output_path}")
                return

    raise RuntimeError("Gemini did not return a generated image.")


# --------------------------------------------------
# Pipeline
# --------------------------------------------------
def main():
    moderation_result = moderate_image(FOREGROUND_IMAGE)
    print("Moderation result:")
    print(moderation_result)

    # Only proceed when Gemini classifies the image as safe.
    if not moderation_result.strip().lower().startswith("safe content"):
        print("Image merge stopped because the foreground image was not classified as Safe Content.")
        return

    merge_images(
        foreground_path=FOREGROUND_IMAGE,
        background_path=BACKGROUND_IMAGE,
        output_path=OUTPUT_IMAGE,
    )


if __name__ == "__main__":
    main()
