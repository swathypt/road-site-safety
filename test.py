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
import sqlite3

# Load API key from environment variable
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

# Define the image folder path
IMAGE_FOLDER = "images"
DB_FILE = "site_violations.db"


# ------------------- DATABASE SETUP -------------------
def get_db_connection():
    """Connects to SQLite and ensures the tables exist."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Table for violations
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Violations (
        Timestamp TEXT,
        Location_ID INTEGER DEFAULT 0,
        Image_Reference TEXT,
        Violation_Type TEXT,
        Risk_Level TEXT
        );
        """)

    conn.commit()
    return conn, cursor


# ------------------- IMAGE PROCESSING -------------------
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
            max_size = 2048  # Limit largest dimension to 2048px for accuracy
            img.thumbnail((max_size, max_size), Image.LANCZOS)   

            # Save to an in-memory buffer instead of a file
            img_buffer = io.BytesIO()
            img.save(img_buffer, format="JPEG", quality=90)  
            img_bytes = img_buffer.getvalue()

            return base64.b64encode(img_bytes).decode("utf-8")
    except Exception as e:
        print(f"Error processing {image_path}: {e}")
        return None


# ------------------- AI ANALYSIS -------------------
def analyze_images(image_paths, prompt, batch_size=2):
    """Processes multiple images, sends batch request to OpenAI, and stores violations in SQLite."""

    def parse_json_responses(response_text):
        """Cleans OpenAI response and extracts JSON objects."""
        clean_response = re.sub(r"```json\n|\n```", "", response_text).strip()
        # Handle multiple JSON blocks, split using `json` keyword separators
        json_objects = re.split(r'\njson\n', clean_response)

        parsed_results = {}
        try:
            for obj_str in json_objects:
                parsed_obj = json.loads(obj_str)
                image_id = parsed_obj.get("image_id", "unknown")
                parsed_results[image_id] = parsed_obj
            
            return parsed_results
        except json.JSONDecodeError as e:
            print(f"❌ JSON Parsing Error: {e}")
            return {"error": "Invalid JSON format", "raw_response": clean_response}

    try:
        results = {}

        for i in range(0, len(image_paths), batch_size):
            batch = image_paths[i:i + batch_size]

            processed_images = [
                {"filename": os.path.basename(path), "base64": process_image(path)}
                for path in batch if process_image(path)
            ]

            if not processed_images:
                print(f"⚠️ No valid images in batch {i // batch_size + 1}")
                continue

            print(f"📸 Sending {len(processed_images)} images to OpenAI...")

            response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "Analyze worker safety compliance in images"},
                    {"role": "user", "content": [
                        {"type": "text", "text": prompt},
                        *[
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img['base64']}"}} 
                            for img in processed_images
                        ]
                    ]}
                ],
                max_tokens=800
            )

            batch_results = parse_json_responses(response.choices[0].message.content)
            results.update(batch_results)

            time.sleep(1)  # Prevent API rate limits

        return results

    except Exception as e:
        print(f"Error in batch processing: {e}")
        return {"error": str(e)}


# ------------------- DEFINE PROMPT -------------------
prompt = """
Analyze this construction site image and return a strict JSON response:

### Workers Detection:
- Detect **all workers** in the image with a confidence score threshold of **≥ 0.7**.
- Ignore **pedestrians, mannequins, shadows, and reflections**.
- Do **not** assume all workers are wearing the correct gear unless clearly visible.
- Return **ALL** workers detected, even if safety status is uncertain.
- Exclude **distant workers** below 2% of the image width/height.

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
      "confidence": 0.95
    }
  ]
}
"""
# ------------------- DATABASE INSERTION -------------------
import os  # Ensure os module is imported

def insert_violations(results):
    """Insert extracted violations into the SQLite database, using 0 for Location_ID."""
    conn, cursor = get_db_connection()

    for image_id, data in results.items():
        # Ensure Image_Reference has the correct file extension
        actual_filename = next((file for file in os.listdir(IMAGE_FOLDER) if file.startswith(image_id)), image_id)
        
        print(f"🖼️ Processing image: {actual_filename}")  # Debugging
        print(f"🔎 Data received: {json.dumps(data, indent=2)}")  # Debugging

        if "violations" in data and data["violations"]:
            # **Insert Violations for this Image**
            for violation in data["violations"]:
                print(f"🚨 Inserting Violation: {violation}")  # Debugging
                cursor.execute("""
                INSERT INTO Violations (Timestamp, Location_ID, Image_Reference, Violation_Type, Risk_Level)
                VALUES (?, ?, ?, ?, ?)
                """, (
                    data["timestamp"],  # Timestamp extracted by model
                    0,  # Set default Location_ID to 0
                    actual_filename,  # Corrected image filename with extension
                    violation["reason"],  # Violation type
                    violation["risk_level"]  # Risk level
                ))

    conn.commit()
    conn.close()
    print("✅ Data successfully inserted into the database!")






# ------------------- PROCESS IMAGES -------------------
if __name__ == "__main__":
    image_files = glob.glob(os.path.join(IMAGE_FOLDER, "*.*"))

    if image_files:
        print(f"🔍 Processing {len(image_files)} images...")
        print(f"🔍 Processing {image_files} images...")
        result = analyze_images(image_files, prompt)  # ✅ Process images
        print(json.dumps(result, indent=2))

        # Insert results into the database
        insert_violations(result)

        print("✅ Data successfully inserted into the database!")
    else:
        print("❌ No valid images found in the directory!")
