from flask import Flask, jsonify, request
from flask_cors import CORS  # ✅ Import CORS
import sqlite3

app = Flask(__name__)
CORS(app)  # ✅ Enable CORS for all routes

DB_FILE = "site_violations.db"

def get_db_connection():
    """Connect to SQLite database."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row  # Enables dictionary-style row access
    return conn

@app.route('/')
def home():
    return "Flask API is running. Use /violations to fetch data."

@app.route('/violations', methods=['GET'])
def get_violations():
    """Fetch violations with optional filters."""
    conn = get_db_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM Violations"
    cursor.execute(query)
    results = cursor.fetchall()
    
    conn.close()
    return jsonify([dict(row) for row in results])

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
