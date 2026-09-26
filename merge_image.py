#merge background with foreground profile picture
import os

from dotenv import load_dotenv
from google import genai
import base64

load_dotenv()
api_key = (
    os.getenv("GEMINI_API_KEY")
 
)

if not api_key:
    raise RuntimeError(
        "Missing API key. Set GOOGLE_API_KEY, GEMINI_API_KEY, or API_KEY in your environment or .env file."
    )

client = genai.Client(api_key=api_key)

with open('sample2.jpg', 'rb') as f:
    dress_bytes = f.read()
with open('background_image.jpg', 'rb') as f:
    model_bytes = f.read()
text_input = """Create a professional mosaic image where the background image is alittle faded and the foreground image is clearly visible. the foreground image should A style sticker. without changing the foreground image. The background image should be faded and the foreground image should be clearly visible. The final image should be a mosaic of the two images, with the foreground image in the center and the background image surrounding it. The final image should be a PNG file with a transparent background. The foreground image should be centered and start from the bottom of the background image"""

interaction = client.interactions.create(
    model="gemini-3.1-flash-image",
    input=[
        {
            "type": "image",
            "data": base64.b64encode(dress_bytes).decode('utf-8'),
            "mime_type": "image/png"
        },
        {
            "type": "image",
            "data": base64.b64encode(model_bytes).decode('utf-8'),
            "mime_type": "image/png"
        },
        {"type": "text", "text": text_input}
    ],
)

for step in interaction.steps:
    if step.type == "model_output":
        for content_block in step.content:
            if content_block.type == "text":
                print(content_block.text)
            elif content_block.type == "image":
                with open("fashion_ecommerce_shot.png", "wb") as f:
                    f.write(base64.b64decode(content_block.data))