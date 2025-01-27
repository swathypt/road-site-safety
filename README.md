# **PPE Compliance Detection System 💪**  

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

## **🗂️ Directory Structure**
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

## **⚙️ Installation & Setup**
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

## **🚀 How It Works**
1. **Image Processing** – Captures images from construction sites.  
2. **AI Analysis** – OpenAI Vision API detects PPE compliance.  
3. **Database Storage** – Results are stored in SQLite.  
4. **Backend API** – Flask serves data via REST API.  
5. **Dashboard** – React frontend visualizes violations, trends, and compliance rates.  

---

## **🛠️ Testing**
To run unit tests:
```bash
cd unit_tests
pytest test_image_processing.py
```

