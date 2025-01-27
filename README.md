# **PPE Compliance Detection System 🚧**  

**Automated monitoring of PPE compliance using AI & Computer Vision.**  

## **📌 Project Overview**  
This project automates the **detection of PPE (Personal Protective Equipment) compliance** at construction sites.  
It uses **computer vision** to analyze images, identify compliance violations, and present structured insights via an interactive dashboard.  

### **✨ Key Features**  
✅ **AI-powered PPE detection** using OpenAI Vision API  
✅ **Flask backend** for data processing and API handling  
✅ **SQLite database** for structured violation tracking  
✅ **React-based dashboard** for visualization and analytics  
✅ **Logging, error handling, and unit testing** for robustness  

---

## **🗂 Directory Structure**
```
road-site-safety/
│── backend/          # Flask API & image processing scripts
│── ppe-dashboard/    # React frontend for visualization
│── unit_tests/       # Unit tests for image processing & API endpoints
│── images/           # Stores input images for testing
│── venv/             # Python virtual environment (ignored in Git)
│── site_violations.db # SQLite database storing violations
│── .gitignore        # Git ignored files (logs, virtual env, etc.)
│── README.md         # Project documentation (this file)
```

---

## **⚙️ Setup Instructions**
### **1️⃣ Clone the Repository**
```bash
git clone https://github.com/your-repo/road-site-safety.git
cd road-site-safety
```

### **2️⃣ Set Up Virtual Environment**
```bash
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
venv\Scripts\activate     # On Windows
```

### **3️⃣ Install Dependencies**
```bash
pip install -r backend/requirements.txt
cd ppe-dashboard
npm install
```

### **4️⃣ Run the Flask Backend**
```bash
cd backend
python app.py
```
*The backend will be available at:* `http://127.0.0.1:5000/`

### **5️⃣ Start the React Dashboard**
```bash
cd ppe-dashboard
npm start
```
*The dashboard will be accessible at:* `http://localhost:3000/`

---

## **📡 API Documentation**
### **Endpoints**
#### **1️⃣ GET /violations**
Retrieves all recorded PPE violations.
```bash
curl -X GET http://127.0.0.1:5000/violations
```
#### **2️⃣ GET /high_risk_areas**
Fetches locations with the highest non-compliance levels.
```bash
curl -X GET http://127.0.0.1:5000/high_risk_areas
```
#### **3️⃣ GET /violation_trends**
Analyzes violation trends over different time periods.
```bash
curl -X GET http://127.0.0.1:5000/violation_trends
```

---

## **🛠️ System Architecture Overview**
```
+--------------------+
|  Image Capture    |
+--------------------+
        ↓
+--------------------+
|  AI Processing    |  -> OpenAI Vision API analyzes images
+--------------------+
        ↓
+--------------------+
|  Data Storage     |  -> SQLite stores structured data
+--------------------+
        ↓
+--------------------+
|  Backend API      |  -> Flask API serves data to frontend
+--------------------+
        ↓
+--------------------+
|  Dashboard UI     |  -> React visualizes insights
+--------------------+
```

---

## **🎯 Prompt Engineering Approach**
### **Optimizing Prompts for OpenAI Vision API**
1. **Structured Formatting**: Ensured input images were correctly formatted and labeled.
2. **Incremental Refinement**: Adjusted prompt wording to improve classification accuracy.
3. **Handling Edge Cases**: Designed prompts to recognize workers **holding PPE** rather than wearing it.
4. **Response Filtering**: Implemented logic to discard vague responses like *"I'm sorry, I can't help with that."*

---

## **📌 Future Improvements**
🔹 Enhance **AI model reliability** (consider LLaMA/Ollama for fine-tuning)  
🔹 Improve **worker recognition** for better accuracy  
🔹 Implement **real-time alerts** for non-compliance  

---
