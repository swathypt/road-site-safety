# Import the required libraries
import openai
import os
import json
import base64
import glob
import re
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

    # 🔹 New table for Sites
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Sites (
        Site_ID INTEGER PRIMARY KEY AUTOINCREMENT,
        Site_Name TEXT UNIQUE
    );
    """)

    # 🔹 Modified Violations table to reference Sites
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Violations (
        ID INTEGER PRIMARY KEY AUTOINCREMENT,
        Timestamp TEXT,
        Site_ID INTEGER,  -- References Sites table
        Image_Reference TEXT,
        Violation_Type TEXT,
        Risk_Level TEXT,
        FOREIGN KEY (Site_ID) REFERENCES Sites (Site_ID)
    );
    """)

    conn.commit()
    return conn, cursor

# ------------------- IMAGE PROCESSING -------------------
def is_valid_image(file_path):
    """Check if file is a valid image with allowed format and size."""
    if not os.path.isfile(file_path):
        print(f"❌ File does not exist: {file_path}")
        return False

    if os.path.getsize(file_path) > MAX_FILE_SIZE:
        print(f"❌ File size exceeds limit: {file_path}")
        return False

    ext = os.path.splitext(file_path)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        print(f"❌ Invalid file format: {file_path}")
        return False

    try:
        with Image.open(file_path) as img:
            img.verify()  # Ensure file is an image
        return True
    except Exception as e:
        print(f"❌ Corrupt image file: {file_path}, Error: {e}")
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


    """Parses JSON responses from OpenAI and maps results to actual filenames."""
    print("response_text", response_text)
    clean_response = re.sub(r"```json\n|\n```", "", response_text).strip()
    json_objects = re.split(r'\njson\n', clean_response)
    print("json_objects", json_objects)
    results = {}

    try:
        for image_path, obj_str in zip(image_paths, json_objects):  # Match each JSON with an image
            try:
                parsed_data = json.loads(obj_str)  # Ensure correct JSON format

                # If OpenAI response is a list of JSON objects instead of a single dictionary
                if isinstance(parsed_data, list):  
                    merged_data = {"image_id": os.path.basename(image_path), "violations": []}

                    # Extract data from each JSON object in the list
                    for obj in parsed_data:
                        merged_data["timestamp"] = obj.get("timestamp", "unknown")
                        merged_data["location_details"] = obj.get("Location details", "unavailable")

                        if "violations" in obj and isinstance(obj["violations"], list):
                            merged_data["violations"].extend(obj["violations"])  # Merge violations

                    results[merged_data["image_id"]] = merged_data  # Store in results dictionary

                elif isinstance(parsed_data, dict):  # Standard single JSON object
                    actual_filename = os.path.basename(image_path)  
                    parsed_data["image_id"] = actual_filename  # Overwrite OpenAI's image_id
                    results[actual_filename] = parsed_data  # Store results under actual filename

                else:
                    print(f"⚠️ Unexpected JSON format for {image_path}: {parsed_data}")
                    continue  # Skip malformed responses

            except json.JSONDecodeError as e:
                print(f"❌ JSON Parsing Error for {image_path}: {e}")
                continue  # Skip errors and continue processing

        return results
    except Exception as e:
        print(f"⚠️ Unexpected Error in parse_json_responses: {e}")
        return {}  # Return an empty dictionary instead of a list

def parse_json_responses(response_text, image_paths):
    """Parses JSON responses from OpenAI and maps results to actual filenames."""
    print("response_text", response_text)
    
    # Remove markdown code fences if present
    clean_response = re.sub(r"```json\n|\n```", "", response_text).strip()
    
    # Split multiple JSON objects if they are separated by '\njson\n'
    json_objects = re.split(r'\njson\n', clean_response)
    print("json_objects", json_objects)
    
    results = {}

    try:
        for image_path, obj_str in zip(image_paths, json_objects):  # Match each JSON with an image
            try:
                parsed_data = json.loads(obj_str)  # Ensure correct JSON format

                # Initialize merged_data with image_id
                merged_data = {"image_id": os.path.basename(image_path)}

                # Extract required fields
                merged_data["timestamp"] = parsed_data.get("timestamp", "unknown")
                merged_data["site_name"] = parsed_data.get("site_name", "unknown")
                merged_data["class_reasoning"] = parsed_data.get("class_reasoning", "")

                # Extract location details if present
                merged_data["location_details"] = parsed_data.get("Location details", "unavailable")

                # Extract violations if present
                if "violations" in parsed_data and isinstance(parsed_data["violations"], list):
                    merged_data["violations"] = parsed_data["violations"]
                else:
                    merged_data["violations"] = []

                results[merged_data["image_id"]] = merged_data  # Store in results dictionary

            except json.JSONDecodeError as e:
                print(f"❌ JSON Parsing Error for {image_path}: {e}")
                continue  # Skip errors and continue processing

        return results
    except Exception as e:
        print(f"⚠️ Unexpected Error in parse_json_responses: {e}")
        return {}  # Return an empty dictionary instead of a list

# ------------------- AI ANALYSIS -------------------
def analyze_images(image_paths, prompt, batch_size=1):
    """Processes images, sends batch requests to OpenAI, and maps results using actual filenames."""

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
                max_tokens=2000
            )

            batch_results = parse_json_responses(response.choices[0].message.content, batch)  # Pass batch image paths
            results.update(batch_results)

            time.sleep(1)  # Prevent API rate limits

        return results

    except Exception as e:
        print(f"Error in batch processing: {e}")
        return {"error": str(e)}

# ------------------- DEFINE PROMPT -------------------
# **Worker Detection Rules**
worker_detection = """
- **Only** classify an individual as a construction worker if:
  1. They appear to be **actively engaged in construction-related tasks** (e.g., operating machinery, handling construction materials, wearing standard construction gear), **AND**
  2. Your detection confidence is **≥ 0.7**.
- Under **no circumstances** classify the following as workers:
  - Pedestrians or bystanders who are merely **walking near** the construction area (including those on footpaths or near construction vehicles who do not appear to be performing construction duties).
  - Mannequins
  - Shadows
  - Reflections
- **Proximity alone** (e.g., “walking near a construction area”) is **not sufficient** to label someone as a worker.
- Do **not** assume workers are wearing the correct gear unless it is clearly visible.
- Return **ALL** workers detected (those genuinely involved in construction), even if safety status is uncertain.
- Exclude “distant workers” if they occupy less than 2% of the image width or height.
- Provide a **class_reasoning** for why each individual was classified as a worker or excluded.
"""
       
# **Hardhat Detection Rules**
hardhat_spec = """
    - **Hardhats** must be strictly limited to **white, yellow, or orange**, based on predefined RGB/HSV color ranges.
    - Do **not** classify **soft hats, beanies, monkey caps, or winter caps** as hardhats.
    - A valid hardhat must be **rigid and worn on the head**.
    - If a worker is **holding** a hardhat instead of wearing it, classify as **"absent"**.
    - If a hardhat is **placed on the floor** instead of being worn, classify as **"absent"**.
    - If **detection confidence is below 0.7**, classify as **"absent"**.
"""

# **Hi-Vis Vest Detection Rules**
hi_vis_spec = """
    - Detect **hi-vis vests** strictly in **yellow or orange**, based on predefined RGB/HSV color ranges.
    - The vest must be **properly worn**—do not classify vests draped over the shoulder.
    - If **detection confidence is below 0.7**, classify as **"absent"**.
    - Ensure vests are not misclassified by distinguishing them from **traffic cones or other similarly colored objects**.
"""

prompt = """

Analyze this construction site for PPE (hardhat + vest) compliance.

- **Include an entry in "violations" for every valid construction worker detected**, regardless of PPE compliance.
- For each worker:
  - If the worker has PPE compliance issues, set "risk_level" accordingly (e.g., "high", "medium").
  - If the worker is fully compliant, set "risk_level" to "compliant".
  - Provide a brief "reason" explaining the compliance status.
- **Exclude** pedestrians, bystanders, mannequins, or any non-worker entities from "violations".

Detect Workers based on {worker_detection}  
if a worker is detected:    
    Detect hardhat status based on {hardhat_spec}
    Detect Hi-vis status based on {hi_vis_spec}
    ### **Site Tracking Rules**
    - Extract **visible site name** from the image if present (e.g., "Trig Road","Compound Section" or "Camera 01").
    - Don't infer Device No as site name.
    - Correct any obvious spelling errors in the site name.
    - If no site can be inferred, return "site_name": "unknown".

    ### Compliance Classification:
    - "high" → No hardhat AND no vest.
    - "medium" → Either hardhat OR vest missing.
    - "compliant" → Both hardhat AND vest present.
    - "unknown" → Unable to determine safety gear due to occlusion or poor visibility.
    - Provide **bounding box coordinates** for each worker in **normalized format (0-1 scale)**.
    - Extract **timestamp** from the image if present (formatted as "YYYY-MM-DDTHH:MM:SSZ"). If missing, return "timestamp": "unknown".
    - Ensure **confidence scores** are included for each detection.

    ### Return ONLY valid JSON—nothing else. No markdown formatting, no code fences. 
    # JSON must look like this:
    json
    {
        "image_id": "<image_filename>",
        "timestamp": "YYYY-MM-DDTHH:MM:SSZ",
        "site_name": "Site Name",
        "class_reasoning": "Explanation of overall site analysis",
        "violations": [
            {
                "worker_id": 1,
                "risk_level": "high",
                "reason": "Worker without hardhat and hi-vis vest",
                "location": {"x": 0.25, "y": 0.40, "width": 0.1, "height": 0.2},
                "confidence": 0.95
            },
            {
                "worker_id": 2,
                "risk_level": "compliant",
                "reason": "Worker wearing hardhat and hi-vis vest",
                "location": {"x": 0.60, "y": 0.50, "width": 0.15, "height": 0.25},
                "confidence": 0.90
            }
        ]
    }
"""

# ------------------- DATABASE INSERTION -------------------
def insert_violations(results):
    """Insert extracted violations into the SQLite database while ensuring consistent site tracking."""
    conn, cursor = get_db_connection()

    for actual_filename, data in results.items():
        print(f"🖼️ Processing image: {actual_filename}")  
        print(f"🔎 Data received: {json.dumps(data, indent=2)}")  

        site_name = data.get("site_name", "unknown")  # Extract inferred site

        # 🔹 Step 1: Check if site already exists
        cursor.execute("SELECT Site_ID FROM Sites WHERE site_name = ?", (site_name,))
        row = cursor.fetchone()

        if row:
            site_id = row[0]  # Existing Site_ID
        else:
            # 🔹 Step 2: Insert new site and get Site_ID
            cursor.execute("INSERT INTO Sites (Site_Name) VALUES (?)", (site_name,))
            site_id = cursor.lastrowid  # Get new Site_ID

        # 🔹 Step 3: Insert violations linked to Site_ID
        if "violations" in data and data["violations"]:
            for violation in data["violations"]:
                print(f"🚨 Inserting Violation: {violation}")  
                cursor.execute("""
                INSERT INTO Violations (Timestamp, Site_ID, Image_Reference, Violation_Type, Risk_Level)
                VALUES (?, ?, ?, ?, ?)
                """, (
                    data["timestamp"],  # Extracted timestamp
                    site_id,  # Linked to Site_ID
                    actual_filename,  # Exact image filename
                    violation["reason"],  # Violation description
                    violation["risk_level"]  # Risk level
                ))

    conn.commit()
    conn.close()
    print("✅ Data successfully inserted into the database!")

# ------------------- PROCESS IMAGES -------------------
if __name__ == "__main__":
    VALID_EXTENSIONS = (".jpg", ".jpeg", ".png", ".bmp", ".gif")
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB limit

    image_files = [
        f for f in glob.glob(os.path.join(IMAGE_FOLDER, "*.*"))
        if f.lower().endswith(VALID_EXTENSIONS)
    ]


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
