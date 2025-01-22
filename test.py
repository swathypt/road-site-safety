import openai
import base64
import os

# Load API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

# Correct the file path
IMAGE_PATH = "images/violation_image_20250120214613_20250121-104605_AIOP_Video_image.jpg"

# Ensure the file exists before proceeding
if not os.path.exists(IMAGE_PATH):
    print(f"Error: File '{IMAGE_PATH}' not found.")
    exit(1)

# Convert image to Base64
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

# Encode the image
base64_image = encode_image(IMAGE_PATH)

# Define the prompt
prompt = "describe about workers detected in detail. How they look, how close are they to truck, ppe compliance etc, Also decribe about the chance of worker to be any other object like cone,signal etc"

# Send request to OpenAI Vision API
response = openai.ChatCompletion.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "You are an AI that provides detailed image descriptions."},
        {"role": "user", "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
        ]}
    ],
    max_tokens=500
)

# Print the response
print(response.choices[0].message.content)
