import openai
import os
import json
import base64
import glob
import re
from PIL import Image
import io
from datetime import datetime

# Load API key from environment variable
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

# Define the image folder path
IMAGE_FOLDER = "images"

def is_valid_image(file_path):
    """Check if the file is a valid image."""
    try:
        with Image.open(file_path) as img:
            img.verify()
        return True
    except:
        return False

def process_image(image_path):
    """Load, resize, and convert an image to a Base64-encoded string."""
    try:
        with Image.open(image_path).convert("RGB") as img:
            # Resize to OpenAI low-cost standard (1024x1024)
            img = img.resize((1024, 1024), Image.LANCZOS)
            
            # Save to an in-memory buffer instead of a file
            img_buffer = io.BytesIO()
            img.save(img_buffer, format="JPEG", quality=85)
            img_bytes = img_buffer.getvalue()

            # Convert to Base64
            return base64.b64encode(img_bytes).decode("utf-8")
    except Exception as e:
        print(f"Error processing {image_path}: {e}")
        return None


def analyze_image(image_path):
    """Analyze image with OpenAI API and return structured JSON output."""
    try:
        base64_image = process_image(image_path)
        if not base64_image:
            return {"error": "Invalid image"}

        # Define optimized prompt to force structured JSON output
        prompt = """Analyze this construction site image and return a strict JSON response:
        - Identify workers in the image.
        - Determine if each worker is wearing a hardhat and a hi-vis vest.
        - Classify violations into:
            - "High Risk" → No hardhat AND no vest.
            - "Medium Risk" → Either hardhat OR vest missing.
            - "Compliant" → Both present.
        - Provide bounding box coordinates for each worker.
        - Fetch timestamp from the image and convert to "2024-01-21T10:30:00Z" format.
        - Output must be strict JSON format as:
        {
          "image_id": "<image_filename>",
          "timestamp": "2024-01-21T10:30:00Z",
          "violations": [
            {
              "risk_level": "high",
              "reason": "Worker without hardhat and hi-vis vest",
              "location": {"x": 100, "y": 200, "width": 50, "height": 100},
              "confidence": 0.95
            }
          ]
        }"""

        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You analyze worker safety compliance in images and return structured JSON."},
                {"role": "user", "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]}
            ],
            max_tokens=200
        )

        # Extract JSON response safely
        response_text = response.choices[0].message.content

        # Fix if OpenAI returns invalid JSON
        json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
        if json_match:
            parsed_json = json.loads(json_match.group(0))

            # Ensure correct image_id and timestamp
            parsed_json["image_id"] = os.path.basename(image_path)
            return parsed_json
        else:
            return {"error": "Invalid JSON format received", "raw_response": response_text}

    except Exception as e:
        print(f"Error processing {image_path}: {e}")
        return {"error": str(e)}

# Process images
if __name__ == "__main__":
    image_files = [f for f in glob.glob(os.path.join(IMAGE_FOLDER, "*.*")) if is_valid_image(f)]
    results = {}

    for image in image_files:
        print(f"Processing: {image}")
        results[image] = analyze_image(image)

    # Print final JSON output
    print(json.dumps(results, indent=2))
