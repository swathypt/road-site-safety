🚧 Road Site Safety Monitoring System📌 Project OverviewThis project is an AI-powered PPE Compliance Monitoring System that detects safety violations in construction sites using computer vision and deep learning. It consists of a Flask backend for image processing and a React frontend for real-time dashboards.
📂 Directory Structure📂 road-site-safety
│── 📂 .git/                # Git repository metadata
│── 📄 README.md            # Project documentation
│── 📄 app.py               # Flask backend
│── 📄 config.yaml          # Configuration settings
│── 📂 dataset/             # Input dataset storage
│── 📄 detect_violations.py # Image processing & AI detection
│── 📂 images/              # Processed image storage
│── 📂 output/              # Processed outputs
│── 📂 ppe-dashboard/       # React frontend (if applicable)
│── 📄 safety_system.log    # Logs for debugging
│── 📄 server.log           # Server activity logs
│── 📄 site_violations.db   # SQLite database for violations
│── 📄 test.py              # Test script for validation
│── 📂 unit_tests/          # Unit testing scripts
│── 📂 venv/                # Virtual environment (ignored in Git)🚀 Setup Instructions🛠 PrerequisitesEnsure you have the following installed:
Python 3.8+
Node.js & npm
SQLite
Git
🔧 Backend Setupcd road-site-safety
python3 -m venv venv
source venv/bin/activate  # (On Windows use `venv\Scripts\activate`)
pip install -r requirements.txt
python app.pyBackend should now be running on http://127.0.0.1:5000/

🎨 Frontend Setupcd ppe-dashboard
npm install
npm startFrontend should now be running on http://localhost:3000/

📡 API DocumentationSee docs/API_documentation.md for complete API endpoints and usage.
Example API Calls:
GET /violations → Fetch all safety violations.
GET /high_risk_areas → Retrieve high-risk locations.
GET /violation_trends → Analyze violation trends over time.

🏗 System Architecture
The system consists of:
React Frontend → User-friendly dashboard
Flask Backend → Image processing & API server
SQLite Database → Stores compliance violations
OpenAI API → Processes images for PPE detection

🎯 Prompt Engineering ApproachWe utilize OpenAI’s GPT-4o for analyzing safety violations. The prompt is optimized for:
✅ Detecting workers vs pedestrians
✅ Identifying PPE compliance (hardhat, vest)
✅ Classifying risk levels
See docs/prompt_engineering.md for full details.

🏁 Future Enhancements✅ Deploy on AWS/GCP
✅ Automate CI/CD with GitHub Actions
✅ Enhance AI model with custom dataset

💡 For any issues, open a GitHub issue or contact swathypt@gmail.com