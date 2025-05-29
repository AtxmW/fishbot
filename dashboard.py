import os
import json
import csv
from flask import Flask, render_template_string

# Set up paths
PROFILE_FILE = "fruit_profiles.json"
CSV_FILE = "fruit_profiles.csv"

# Load profiles
def load_profiles():
    if not os.path.exists(PROFILE_FILE):
        return []
    with open(PROFILE_FILE, "r") as f:
        return json.load(f)

# Export to CSV
def export_to_csv():
    profiles = load_profiles()
    if not profiles:
        return "No profiles to export."

    fieldnames = ["name", "number", "socials", "submitted_by", "timestamp"]
    with open(CSV_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for p in profiles:
            row = {k: ", ".join(v) if isinstance(v, list) else v for k, v in p.items()}
            writer.writerow(row)
    return f"{len(profiles)} profiles exported to {CSV_FILE}"

# Flask app
app = Flask(__name__)

@app.route("/")
def dashboard():
    profiles = load_profiles()
    html = """
    <html>
    <head>
        <title>Fruit Profiles Dashboard</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 2em; }
            table { border-collapse: collapse; width: 100%; }
            th, td { border: 1px solid #ccc; padding: 10px; text-align: left; }
            th { background-color: #f0f0f0; }
        </style>
    </head>
    <body>
        <h2>🍉 Fruit Profiles Dashboard</h2>
        <p>Total Profiles: {{ profiles|length }}</p>
        <table>
            <tr>
                <th>Name</th>
                <th>Number</th>
                <th>Socials</th>
                <th>Submitted By</th>
                <th>Timestamp</th>
            </tr>
            {% for p in profiles %}
            <tr>
                <td>{{ p.get('name', '') }}</td>
                <td>{{ p.get('number', '') }}</td>
                <td>{{ ", ".join(p.get('socials', [])) }}</td>
                <td>{{ p.get('submitted_by', '') }}</td>
                <td>{{ p.get('timestamp', '') }}</td>
            </tr>
            {% endfor %}
        </table>
    </body>
    </html>
    """
    return render_template_string(html, profiles=profiles)

if __name__ == "__main__":
    print(export_to_csv())
    app.run(debug=True)
