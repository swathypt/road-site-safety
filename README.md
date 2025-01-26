# 🚧 Road Site Safety Compliance System

## 📌 Overview
The **Road Site Safety Compliance System** is an AI-driven prototype that automates the detection and classification of **Personal Protective Equipment (PPE) compliance violations** at construction sites. Using **computer vision**, **OpenAI Vision API**, and **real-time data processing**, this system enables enhanced safety monitoring and reporting.

## 🎯 Features
- **Automated PPE Compliance Detection**: Classifies workers into **High Risk, Medium Risk, or Compliant** categories.
- **AI-Powered Image Analysis**: Uses OpenAI Vision API to detect **hardhats and hi-vis vests**.
- **Real-time Data Processing**: Tracks **violations, compliance trends, and high-risk areas**.
- **Interactive Dashboard**: Built with **React.js**, featuring visualizations via **Chart.js**.
- **REST API for Data Retrieval**: Backend powered by **Flask & SQLite** for efficient data management.
- **Security Best Practices**: API key protection, structured logging, and robust error handling.

## 🏗️ System Architecture
```
📂 road-site-safety-compliance
│── backend
│   ├── app.py                # Flask API for serving violations data
│   ├── detect_violations.py  # Image processing & AI model integration
│   ├── site_violations.db    # SQLite database storing compliance data
│── frontend
│   ├── App.js                # React-based dashboard
│   ├── App.css               # Styling for UI components
│── images                    # Directory for storing processed site images
│── README.md                 # Project documentation
```

## 🛠️ Installation & Setup
### 1️⃣ Clone the Repository
```sh
 git clone https://github.com/swathypt/road-site-safety.git
 cd road-site-safety-compliance
```
### 2️⃣ Backend Setup
#### 🔹 Install dependencies
```sh
 cd backend
 pip install -r requirements.txt
```
#### 🔹 Set up environment variables
Create a `.env` file and add your **OpenAI API Key**:
```
OPENAI_API_KEY=your_api_key_here
```
#### 🔹 Run the Flask API
```sh
 python app.py
```
API will be available at: **http://127.0.0.1:5000**

### 3️⃣ Frontend Setup
#### 🔹 Install dependencies
```sh
 cd frontend
 npm install
```
#### 🔹 Run the React app
```sh
 npm start
```
Dashboard available at: **http://localhost:3000**

## 🔗 API Endpoints
| Endpoint                  | Method | Description |
|---------------------------|--------|-------------|
| `/violations`            | GET    | Fetch all recorded violations |
| `/high_risk_areas`       | GET    | Identify high-risk construction sites |
| `/violation_trends`      | GET    | Fetch historical safety violation trends |
| `/compliance_rates`      | GET    | Get site-specific compliance rates |
| `/images/<filename>`     | GET    | Retrieve stored violation images |

## 📊 Data Model (SQLite)
| Column Name       | Type  | Description |
|-------------------|-------|-------------|
| `ID`             | INT   | Unique violation ID |
| `Timestamp`      | TEXT  | Date & time of violation |
| `Site_ID`        | INT   | Foreign key referencing sites |
| `Image_Reference`| TEXT  | Image file name |
| `Violation_Type` | TEXT  | Type of PPE violation |
| `Risk_Level`     | TEXT  | Risk classification (High, Medium, Compliant) |

## 🚀 Future Enhancements
- **Live CCTV Integration** for real-time safety monitoring.
- **Advanced AI Model** for improved object detection and occlusion handling.
- **Mobile App Support** for on-site safety alerts.

## 🔒 Security Best Practices
- **Store API keys securely** (never commit them to GitHub).
- **Use environment variables** for sensitive credentials.
- **Implement user authentication** for real-world deployment.

## 📝 License
This project is licensed under the **MIT License**.

## 🙌 Acknowledgements
- OpenAI for providing **Vision API**.
- React.js & Flask communities for their amazing frameworks.

---

🚧 **Road Site Safety Compliance System - Making Construction Sites Safer!** 🚧

