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

    # Table to track image locations
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Images (
        Location_ID INTEGER PRIMARY KEY AUTOINCREMENT,
        Image_Reference TEXT UNIQUE NOT NULL
    );
    """)

    # Table for violations
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Violations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        Timestamp TEXT NOT NULL,
        Location_ID INTEGER NOT NULL,
        Violation_Type TEXT NOT NULL,
        Risk_Level TEXT NOT NULL,
        FOREIGN KEY (Location_ID) REFERENCES Images(Location_ID)
    );
    """)

    conn.commit()
    return conn, cursor  # ✅ Ensure both connection and cursor are returned



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

# ------------------- AI ANALYSIS -------------------
def analyze_images(image_paths):
    """Analyzes multiple images using OpenAI API and stores violations in SQLite."""
    try:
        processed_images = []
        
        for image_path in image_paths:
            base64_image = process_image(image_path)
            if base64_image:
                processed_images.append({
                    "filename": os.path.basename(image_path),
                    "base64": base64_image
                })
        ######################################TESTING############################################        
        print(f"📸 Sending {len(processed_images)} images to OpenAI...")
        # Ensure all images are being processed
        for img in processed_images:
            print(f"🔹 Image included in request: {img['filename']}")

        if not processed_images:
            return {"error": "No valid images"}

        # Define Prompt Segments
        worker_detection = """
        - Detect **all workers** in the image with a confidence score threshold of **≥ 0.7**.
        - Ignore **pedestrians, mannequins, shadows, and reflections**.
		- Do **not** assume all workers are wearing the correct gear unless clearly visible.
        - Return **ALL** workers detected, even if safety status is uncertain.
        - Exclude **distant workers** below 2 percentage of the image width/height.
        """
        
        # **Hardhat Detection Rules**
        hardhat_spec = """
        - Detect **hardhats** in **white, yellow, or orange**, using predefined RGB/HSV color ranges.
        - Do **not** count **soft hats, beanies, monkey caps, or winter caps** as hardhats.
        - Hardhat must be **rigid and worn on the head**.
        - If a worker is **holding** a hardhat instead of wearing it, classify as **"absent"**.
        - If a hardhat placed on floor instead of wearing it, classify as **"absent"**.
        - If **confidence < 0.7**, classify as **"absent"**.
        """

        # **Hi-Vis Vest Detection Rules**
        hi_vis_spec = """
        - Detect **hi-vis vests** in **yellow or orange**, using predefined RGB/HSV color ranges.
        - Vest must be **actively worn**, not draped over the shoulder.
        - If **confidence < 0.7**, classify as **"absent"**.
        - Avoid misclassifying **traffic cones or other objects similar to vest color** as hi-vis vests.
        """

        prompt = """
        
        Analyze this construction site image and return a strict JSON response:

        Detect Workers based on {worker_detection}      
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
              "confidence": 0.95
            }
          ]
        }
        ```"""

        # Send Batch Request to OpenAI
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You analyze worker safety compliance in images."},
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

        # Extract JSON response safely
        response_text = response.choices[0].message.content
        print("🔍 OpenAI Raw Response:", response_text)  # ✅ Debugging Step

        try:
            # ✅ Remove markdown formatting (```json ... ```) before extracting JSON
            clean_response = re.sub(r"```json\n|\n```", "", response_text).strip()

            # ✅ Extract multiple JSON objects separately
            json_objects = re.findall(r"\{.*?\}", clean_response, re.DOTALL)

            # ✅ Convert extracted JSON strings into Python dictionaries
            parsed_json_list = [json.loads(obj) for obj in json_objects]

            # ✅ Merge results into a structured dictionary
            results = {img["image_id"]: img for img in parsed_json_list}

        except json.JSONDecodeError as e:
            print(f"❌ JSON Parsing Error: {e}")
            return {"error": "Invalid JSON format received", "raw_response": response_text}


        return results  # ✅ Now correctly structured as a dictionary



        # ------------------- STORE RESULTS IN DATABASE -------------------
        conn, cursor = get_db_connection()

        # 🔹 Ensure `image_id` exists in the response
        if "image_id" in parsed_json:
            image_id = parsed_json["image_id"]  # ✅ Extract actual image reference

            # 🔹 Check if the image already exists in the `Images` table
            cursor.execute("SELECT Location_ID FROM Images WHERE Image_Reference = ?", (image_id,))
            existing_location = cursor.fetchone()

            if existing_location:
                location_id = existing_location[0]  # ✅ Reuse existing Location_ID
            else:
                # 🔹 Insert new image reference and fetch Location_ID
                cursor.execute("INSERT INTO Images (Image_Reference) VALUES (?)", (image_id,))
                location_id = cursor.lastrowid

            # 🔹 Extract violations correctly
            violations = parsed_json.get("violations", [])  # ✅ Extract directly from root level

            if violations:  # Ensure there are violations before inserting
                for worker in violations:
                    cursor.execute("""
                    INSERT INTO Violations (Timestamp, Location_ID, Image_Reference, Violation_Type, Risk_Level)
                    VALUES (?, ?, ?, ?, ?)
                    """, (
                        parsed_json["timestamp"],  # ✅ Correct timestamp
                        location_id,  # ✅ Correct location ID
                        image_id,  # ✅ Ensure correct image reference
                        worker["reason"],
                        worker["risk_level"]
                    ))

                conn.commit()  # ✅ Ensure changes are committed
                print(f"✅ Data successfully inserted for {image_id}")
            else:
                print(f"⚠️ No violations detected for {image_id}. Skipping database insertion.")

        else:
            print("❌ Error: `image_id` missing from API response.")

        conn.close()  # ✅ Ensure connection is closed properly



        return parsed_json

    except Exception as e:
        print(f"Error processing images: {e}")
        return {"error": str(e)}

# ------------------- PROCESS IMAGES -------------------
if __name__ == "__main__":
    image_files = glob.glob(os.path.join(IMAGE_FOLDER, "*.*"))  # Get list of image files

    if image_files:
        print(f"🔍 Processing {len(image_files)} images...")
        result = analyze_images(image_files)  # ✅ Pass the entire list
        print(json.dumps(result, indent=2))
    else:
        print("❌ No valid images found in the directory!")
