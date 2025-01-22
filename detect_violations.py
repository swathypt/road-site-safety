import openai
import os
import json
import base64
import glob
import re
import cv2
from PIL import Image
import io
import time


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
    """Load, resize while maintaining aspect ratio, and convert an image to Base64."""
    try:
        with Image.open(image_path).convert("RGB") as img:
            # Keep aspect ratio while resizing (limit the largest dimension to 2048px for better accuracy)
            max_size = 2048
            img = img.resize((max_size, max_size), Image.LANCZOS)   

            # Save to an in-memory buffer instead of a file
            img_buffer = io.BytesIO()
            img.save(img_buffer, format="JPEG", quality=90)  # Higher quality to retain details
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

        # **Hardhat Detection Rules**
        hardhat_spec = """
        - Detect **hardhats** in **white, yellow, or orange**, using predefined RGB/HSV color ranges.
        - Do **not** count **soft hats, beanies, monkey caps, or winter caps** as hardhats.
        - Hardhat must be **rigid and worn on the head**.
        - If a worker is **holding** a hardhat instead of wearing it, classify as **"absent"**.
        - If a hardhat placed on floor instead of wearing it, classify as **"absent"**.
        - If **confidence < 0.7**, classify as **"absent"**.
        """

        # 🔹 **Hi-Vis Vest Detection Rules**
        hi_vis_spec = """
        - Detect **hi-vis vests** in **yellow or orange**, using predefined RGB/HSV color ranges.
        - Vest must be **actively worn**, not draped over the shoulder.
        - If **confidence < 0.7**, classify as **"absent"**.
        - Avoid misclassifying **traffic cones or other objects similar to vest color** as hi-vis vests.
        """

        prompt = """
        
        Analyze this construction site image and return a strict JSON response:

        ### Workers Detection:
        - Detect **all workers** in the image with a confidence score threshold of **≥ 0.7**.
        - Ignore **pedestrians, mannequins, shadows, and reflections**.
		- Do **not** assume all workers are wearing the correct gear unless clearly visible.
        - Return **ALL** workers detected, even if safety status is uncertain.
        - Exclude **distant workers** below 2 percentage of the image width/height.

        Detect hardhat status based on {hardhat_spec}
        Detect Hi-vis status based on {hi_vis_spec}

        ### Compliance Classification:
        - `"high"` → No hardhat AND no vest.
        - `"medium"` → Either hardhat OR vest missing.
        - `"compliant"` → Both hardhat AND vest present.
        - `"unknown"` → Unable to determine safety gear due to occlusion or poor visibility.
        - Provide **bounding box coordinates** for each worker in **normalized format (0-1 scale)**.
        - Extract **timestamp** from the image if present (formatted as `"YYYY-MM-DDTHH:MM:SSZ"`). If missing, return `"timestamp": "unknown"`.

        ### Strict JSON Output Format:
        ```json
        {
          "image_id": "<image_filename>",
          "timestamp": "YYYY-MM-DDTHH:MM:SSZ",
          "violations": [
            {
              "worker_id": 1,
              "risk_level": "high",
              "reason": "Worker without hardhat and hi-vis vest",
              "location": {"x": 0.25, "y": 0.40, "width": 0.1, "height": 0.2},
              "confidence": 0.95,
              "gear_confidence": {
                  "hardhat": 0.85,
                  "hi_vis_vest": 0.90
              }
            }
          ]
        }
        ```"""


        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You analyze worker safety compliance in images and return structured JSON."},
                {"role": "user", "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]}
            ],
            max_tokens=400
        )

        # Extract JSON response safely
        response_text = response.choices[0].message.content

        # Fix if OpenAI returns invalid JSON
        json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
        if json_match:
            parsed_json = json.loads(json_match.group(0))

            # Ensure correct image_id and timestamp
            parsed_json["image_id"] = os.path.basename(image_path)

            # If timestamp is missing, set to "unknown"
            if "timestamp" not in parsed_json or parsed_json["timestamp"] == "":
                parsed_json["timestamp"] = "unknown"

            return parsed_json
        else:
            return {"error": "Invalid JSON format received", "raw_response": response_text}

    except Exception as e:
        print(f"Error processing {image_path}: {e}")
        return {"error": str(e)}

# Process images one by one and print results immediately
if __name__ == "__main__":
    image_files = [f for f in glob.glob(os.path.join(IMAGE_FOLDER, "*.*")) if is_valid_image(f)]

    for image in image_files:
        print(f"🔍 Processing: {image}")

        # Analyze and print results immediately
        result = analyze_image(image)
        print(json.dumps({image: result}, indent=2))
        time.sleep(0.5)  # Prevent API overload