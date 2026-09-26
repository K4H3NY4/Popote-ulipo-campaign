import os
import uuid
import base64
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_from_directory
from dotenv import load_dotenv
from google import genai

load_dotenv()

app = Flask(__name__)

# Configurations
UPLOAD_FOLDER = Path("uploads")
OUTPUT_FOLDER = Path("static/outputs")
BACKGROUND_IMAGE_PATH = Path("background_image.jpg")

UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["OUTPUT_FOLDER"] = OUTPUT_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB limit

# Initialize Gemini Client
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError("Missing GEMINI_API_KEY in environment or .env file.")

client = genai.Client(api_key=api_key)


def moderate_image(image_path: str) -> dict:
    """Classifies image using Gemini Vision moderation."""
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

    result_text = (interaction.output_text or "").strip()
    is_safe = result_text.lower().startswith("safe content")
    return {"is_safe": is_safe, "feedback": result_text}


def generate_merged_image(foreground_path: str, background_path: str, output_path: str) -> None:
    """Merges foreground and background image using Gemini Image generation."""
    with open(foreground_path, "rb") as f:
        foreground_bytes = f.read()

    with open(background_path, "rb") as f:
        background_bytes = f.read()

    merge_prompt = (
        "Create a professional mosaic image where the background image is alittle faded with a dark overlay and the foreground image is clearly visible. the foreground image should A style sticker. without changing the foreground image. The background image should be faded and the foreground image should be clearly visible. The final image should be a mosaic of the two images, with the foreground image in the center and the background image surrounding it. The foreground image should be centered and start from the bottom of the background image"
    )

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
            if content_block.type == "image":
                with open(output_path, "wb") as f:
                    f.write(base64.b64decode(content_block.data))
                return

    raise RuntimeError("Gemini did not return a generated image.")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    if "image" not in request.files:
        return jsonify({"success": False, "error": "No image file uploaded."}), 400

    file = request.files["image"]
    if file.filename == "":
        return jsonify({"success": False, "error": "No file selected."}), 400

    if not BACKGROUND_IMAGE_PATH.exists():
        return jsonify({"success": False, "error": "Default background_image.jpg not found on server."}), 500

    unique_id = uuid.uuid4().hex
    ext = os.path.splitext(file.filename)[1] or ".jpg"
    uploaded_filename = f"upload_{unique_id}{ext}"
    output_filename = f"mosaic_{unique_id}.png"

    input_path = UPLOAD_FOLDER / uploaded_filename
    output_path = OUTPUT_FOLDER / output_filename

    file.save(str(input_path))

    try:
        # Step 1: Content Moderation
        mod_result = moderate_image(str(input_path))
        if not mod_result["is_safe"]:
            return jsonify({
                "success": False,
                "moderation_failed": True,
                "error": "Image violated safety policies.",
                "details": mod_result["feedback"]
            }), 400

        # Step 2: Merge / Generate Image
        generate_merged_image(
            foreground_path=str(input_path),
            background_path=str(BACKGROUND_IMAGE_PATH),
            output_path=str(output_path),
        )

        return jsonify({
            "success": True,
            "original_url": f"/uploads/{uploaded_filename}",
            "generated_url": f"/static/outputs/{output_filename}",
            "moderation": mod_result["feedback"]
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)