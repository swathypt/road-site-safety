from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
import logging
from datetime import datetime
from flask import send_from_directory
import os

# Initialize Flask App
app = Flask(__name__)
CORS(app)
DB_FILE = "site_violations.db"
IMAGE_FOLDER = os.path.join(os.getcwd(), "images")  # Ensure absolute path

# Configure Logging
logging.basicConfig(
    filename='server.log', level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Error Handler
@app.errorhandler(Exception)
def handle_exception(e):
    logging.error(f"Unhandled Exception: {e}")
    return jsonify({"error": "Internal Server Error", "details": str(e)}), 500

# Database Connection
def get_db_connection():
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row  # Enables dictionary-style row access
        return conn
    except sqlite3.Error as e:
        logging.error(f"Database Connection Error: {e}")
        return None

@app.route('/')
def home():
    return "Flask API is running. Use /violations, /high_risk_areas, /violation_trends, or /compliance_rates to fetch data."

# Serve Images Safely
@app.route('/images/<path:filename>')
def serve_image(filename):
    try:
        return send_from_directory(IMAGE_FOLDER, filename)
    except Exception as e:
        logging.error(f"Error serving image {filename}: {e}")
        return jsonify({"error": "Image not found"}), 404

@app.route('/violations', methods=['GET'])
def get_violations():
    try:
        conn = get_db_connection()
        if conn is None:
            return jsonify({"error": "Database connection failed"}), 500

        cursor = conn.cursor()
        query = """
        SELECT v.ID, 
               strftime('%Y-%m-%d', v.Timestamp) AS Date, 
               strftime('%H:%M:%S', v.Timestamp) AS Time,
               s.Site_Name, 
               v.Image_Reference, 
               v.Violation_Type, 
               v.Risk_Level
        FROM Violations v
        JOIN Sites s ON v.Site_ID = s.Site_ID
        ORDER BY v.Timestamp DESC
        """
        cursor.execute(query)
        results = cursor.fetchall()
        conn.close()

        logging.info(f"Fetched {len(results)} violations from the database")
        return jsonify([dict(row) for row in results])
    except Exception as e:
        logging.error(f"Error fetching violations: {e}")
        return jsonify({"error": "Failed to fetch violations", "details": str(e)}), 500

@app.route('/high_risk_areas', methods=['GET'])
def get_high_risk_areas():
    try:
        conn = get_db_connection()
        if conn is None:
            return jsonify({"error": "Database connection failed"}), 500

        cursor = conn.cursor()
        query = """
        SELECT s.Site_ID, s.Site_Name,
               SUM(CASE WHEN v.Risk_Level = 'compliant' THEN 1 ELSE 0 END) AS compliant,
               SUM(CASE WHEN v.Risk_Level = 'medium' THEN 1 ELSE 0 END) AS medium,
               SUM(CASE WHEN v.Risk_Level = 'high' THEN 1 ELSE 0 END) AS high,
               COUNT(v.ID) AS Total_Violations
        FROM Sites s
        LEFT JOIN Violations v ON s.Site_ID = v.Site_ID
        GROUP BY s.Site_ID
        ORDER BY high DESC
        """
        cursor.execute(query)
        sites = cursor.fetchall()
        conn.close()

        results = []
        for site in sites:
            compliant = site["compliant"] or 0
            medium = site["medium"] or 0
            high = site["high"] or 0
            total_violations = site["Total_Violations"] or 0
            risk_score = round(((0 * compliant) + (50 * medium) + (100 * high)) / total_violations, 1) if total_violations > 0 else 0.0

            results.append({
                "Site_ID": site["Site_ID"],
                "Site_Name": site["Site_Name"],
                "Total_Violations": total_violations,
                "Risk_Breakdown": {"compliant": compliant, "medium": medium, "high": high},
                "Risk_Score": risk_score
            })

        logging.info("Fetched high-risk area data")
        return jsonify(results)
    except Exception as e:
        logging.error(f"Error fetching high-risk areas: {e}")
        return jsonify({"error": "Failed to fetch high-risk areas", "details": str(e)}), 500

@app.route('/compliance_rates', methods=['GET'])
def get_compliance_rates():
    try:
        conn = get_db_connection()
        if conn is None:
            return jsonify({"error": "Database connection failed"}), 500

        cursor = conn.cursor()
        query = """
        SELECT S.Site_ID, S.Site_Name, V.Risk_Level, COUNT(*) AS Count
        FROM Violations V
        JOIN Sites S ON V.Site_ID = S.Site_ID
        GROUP BY S.Site_ID, S.Site_Name, V.Risk_Level;
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()

        site_data = {}
        for row in rows:
            site_id = row["Site_ID"]
            site_name = row["Site_Name"]
            risk_level = row["Risk_Level"]
            count = row["Count"]

            if site_name not in site_data:
                site_data[site_name] = {"Site_ID": site_id, "Total_Violations": 0, "Risk_Level_Counts": {}}

            site_data[site_name]["Total_Violations"] += count
            site_data[site_name]["Risk_Level_Counts"][risk_level] = count

        for site in site_data.values():
            compliant_count = site["Risk_Level_Counts"].get("compliant", 0)
            total_violations = site["Total_Violations"]
            site["Compliance_Rate"] = round((compliant_count / total_violations) * 100, 2) if total_violations > 0 else 0

        logging.info("Fetched compliance rates data")
        return jsonify(site_data)
    except Exception as e:
        logging.error(f"Error fetching compliance rates: {e}")
        return jsonify({"error": "Failed to fetch compliance rates", "details": str(e)}), 500
@app.route('/violation_trends', methods=['GET'])
def get_violation_trends():
    try:
        conn = get_db_connection()
        if conn is None:
            return jsonify({"error": "Database connection failed"}), 500
        
        cursor = conn.cursor()
        query = """
        SELECT v.Timestamp, v.Risk_Level
        FROM Violations v
        """
        cursor.execute(query)
        violations = cursor.fetchall()
        conn.close()

        time_slots = {
            "Morning (06:00 - 12:00)": {"compliant": 0, "medium": 0, "high": 0},
            "Afternoon (12:00 - 18:00)": {"compliant": 0, "medium": 0, "high": 0},
            "Evening (18:00 - 00:00)": {"compliant": 0, "medium": 0, "high": 0},
            "Night (00:00 - 06:00)": {"compliant": 0, "medium": 0, "high": 0},
        }
        
        for violation in violations:
            timestamp = violation["Timestamp"]
            risk_level = violation["Risk_Level"].lower() if violation["Risk_Level"] else "unknown"
            
            if risk_level not in ["compliant", "medium", "high"]:
                risk_level = "unknown"
            
            try:
                hour = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ").hour
            except ValueError:
                continue
            
            if 6 <= hour < 12:
                slot = "Morning (06:00 - 12:00)"
            elif 12 <= hour < 18:
                slot = "Afternoon (12:00 - 18:00)"
            elif 18 <= hour < 24:
                slot = "Evening (18:00 - 00:00)"
            else:
                slot = "Night (00:00 - 06:00)"
            
            time_slots[slot][risk_level] += 1
        
        logging.info("Fetched violation trends data")
        return jsonify(time_slots)
    except Exception as e:
        logging.error(f"Error fetching violation trends: {e}")
        return jsonify({"error": "Failed to fetch violation trends", "details": str(e)}), 500

if __name__ == '__main__':
    logging.info("Starting Flask API...")
    app.run(debug=True, host='0.0.0.0', port=5000)
