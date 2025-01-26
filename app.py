from flask import Flask, jsonify
from flask_cors import CORS
import sqlite3
from datetime import datetime
from flask import send_from_directory
import os

app = Flask(__name__)
CORS(app)

DB_FILE = "site_violations.db"


IMAGE_FOLDER = os.path.join(os.getcwd(), "images")  # Ensure absolute path

@app.route('/images/<path:filename>')
def serve_image(filename):
    """Serve images from the images directory"""
    return send_from_directory(IMAGE_FOLDER, filename)

def get_db_connection():
    """Connect to SQLite database."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row  # Enables dictionary-style row access
    return conn

@app.route('/')
def home():
    return "Flask API is running. Use /violations, /high_risk_areas, /violation_trends, or /compliance_rates to fetch data."

@app.route('/violations', methods=['GET'])
def get_violations():
    """Fetch violations with site details, formatted date & time."""
    conn = get_db_connection()
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
    return jsonify([dict(row) for row in results])



@app.route('/high_risk_areas', methods=['GET'])
def get_high_risk_areas():
    """Aggregates violations per site and calculates risk levels."""
    conn = get_db_connection()
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

        # Risk Score Calculation
        if total_violations > 0:
            risk_score = round(((0 * compliant) + (50 * medium) + (100 * high)) / total_violations, 1)
        else:
            risk_score = 0.0

        results.append({
            "Site_ID": site["Site_ID"],
            "Site_Name": site["Site_Name"],
            "Total_Violations": total_violations,
            "Risk_Breakdown": {
                "compliant": compliant,
                "medium": medium,
                "high": high
            },
            "Risk_Score": risk_score
        })

    return jsonify(results)

@app.route('/violation_trends', methods=['GET'])
def get_violation_trends():
    """Tracks violations across different times of the day."""
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
    SELECT v.Timestamp, v.Risk_Level
    FROM Violations v
    """

    cursor.execute(query)
    violations = cursor.fetchall()
    conn.close()

    # Initialize time slots
    time_slots = {
        "Morning (06:00 - 12:00)": {"compliant": 0, "medium": 0, "high": 0, "total": 0},
        "Afternoon (12:00 - 18:00)": {"compliant": 0, "medium": 0, "high": 0, "total": 0},
        "Evening (18:00 - 00:00)": {"compliant": 0, "medium": 0, "high": 0, "total": 0},
        "Night (00:00 - 06:00)": {"compliant": 0, "medium": 0, "high": 0, "total": 0},
    }

    # Process violations
    for violation in violations:
        timestamp = violation["Timestamp"]
        risk_level = violation["Risk_Level"]

        # Extract hour
        try:
            hour = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ").hour
        except ValueError:
            continue  # Skip malformed timestamps

        # Determine time slot
        if 6 <= hour < 12:
            slot = "Morning (06:00 - 12:00)"
        elif 12 <= hour < 18:
            slot = "Afternoon (12:00 - 18:00)"
        elif 18 <= hour < 24:
            slot = "Evening (18:00 - 00:00)"
        else:
            slot = "Night (00:00 - 06:00)"

        # Increment counts
        time_slots[slot][risk_level] += 1
        time_slots[slot]["total"] += 1

    return jsonify(time_slots)

@app.route('/compliance_rates', methods=['GET'])
def get_compliance_rates():
    """Fetch compliance rates by site."""
    conn = get_db_connection()
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

    # Process results into desired format
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

    # Calculate compliance rates
    for site in site_data.values():
        compliant_count = site["Risk_Level_Counts"].get("compliant", 0)
        total_violations = site["Total_Violations"]
        site["Compliance_Rate"] = round((compliant_count / total_violations) * 100, 2) if total_violations > 0 else 0

    return jsonify(site_data)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
