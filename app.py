from flask import Flask, render_template, request, flash, redirect, url_for
import mysql.connector
import csv
import os
from mysql.connector import Error

app = Flask(__name__)
app.secret_key = 'dev_secret_key_change_in_prod'

DB_CONFIG = {
    'host': 'db',
    'user': 'root',
    'password': open('/run/secrets/mysql_root_password', 'r').read().strip() if os.path.exists('/run/secrets/mysql_root_password') else 'secure_root_password_123',
}

def get_db_connection(use_db=True):
    try:
        config = DB_CONFIG.copy()
        if use_db:
            config['database'] = 'mh370_db'
        conn = mysql.connector.connect(**config)
        return conn
    except Error as e:
        print(f"DB Error: {e}")
        return None

def init_db():
    # Connect without specifying database to create it
    conn = get_db_connection(use_db=False)
    if not conn:
        print("Failed to connect to MySQL")
        return
    cursor = conn.cursor()
    try:
        # Create database if it doesn't exist
        cursor.execute("CREATE DATABASE IF NOT EXISTS mh370_db")
        conn.commit()
    except Error as e:
        print(f"Error creating database: {e}")
    cursor.close()
    conn.close()

    # Reconnect with the database
    conn = get_db_connection()
    if not conn:
        print("Failed to connect to mh370_db")
        return
    cursor = conn.cursor()
    try:
        # Create passengers table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS passengers (
                id INT AUTO_INCREMENT PRIMARY KEY,
                sno INT,
                first_name VARCHAR(255),
                last_name VARCHAR(255),
                nationality VARCHAR(255),
                source_airport VARCHAR(255),
                dest_airport VARCHAR(255),
                boarding_purpose VARCHAR(255),
                seat_number VARCHAR(255)
            )
        """)
        # Check if table is empty; if so, import CSV
        cursor.execute("SELECT COUNT(*) FROM passengers")
        if cursor.fetchone()[0] == 0:
            with open('Flight-MH370.csv', 'r') as file:
                csv_reader = csv.DictReader(file)
                for row in csv_reader:
                    cursor.execute("""
                        INSERT INTO passengers (sno, first_name, last_name, nationality, source_airport, dest_airport, boarding_purpose, seat_number)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (row['S.No'], row['FirstName'], row['LastName'], row['Nationality'], row['SourceAirportName'], row['DestinationAirportName'], row['Boarding Purpose'], row['SeatNumber']))
            conn.commit()
    except Error as e:
        print(f"Error initializing table or importing CSV: {e}")
    finally:
        cursor.close()
        conn.close()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'admin' and password == 'mh370admin':
            flash('Login successful!')
            return redirect(url_for('home'))
        flash('Invalid credentials')
    return render_template('login.html')

@app.route('/news')
def news():
    news_items = [
        {
            "title": "MH370 Search Resumes Under New Agreement",
            "date": "March 19, 2025",
            "content": "Malaysia finalizes no-find, no-fee deal with Ocean Infinity to restart wreckage search in the Indian Ocean.",
            "source": "Reuters"
        },
        {
            "title": "Ocean Infinity Leads Fourth Major Search Campaign",
            "date": "May 16, 2025",
            "content": "Exploration resumes in southern Indian Ocean; families hail progress after 11-year wait.",
            "source": "Maritime Crimes"
        },
        {
            "title": "Data Analysis Points to New Wreckage Sites",
            "date": "April 16, 2025",
            "content": "Malaysian cabinet authorizes expanded scan based on satellite and drift models.",
            "source": "The Diplomat"
        },
        {
            "title": "'Black Hole' Theory Gains Traction",
            "date": "August 5, 2025",
            "content": "New hypothesis suggests plane entered uncharted ocean trench; 30+ debris pieces analyzed.",
            "source": "Economic Times"
        },
        {
            "title": "Public Presentation on Evidence Set for October",
            "date": "September 16, 2025",
            "content": "Captain Turner to outline drift evidence supporting resumed search in Perth.",
            "source": "PPRuNe Forums"
        }
    ]
    return render_template('news.html', news=news_items)

@app.route('/passengers')
def passengers():
    conn = get_db_connection()
    if not conn:
        return "DB connection failed", 500
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM passengers ORDER BY sno")
        passengers = cursor.fetchall()
    except Error as e:
        print(f"Error fetching passengers: {e}")
        return "Error fetching passengers", 500
    finally:
        cursor.close()
        conn.close()
    return render_template('passengers.html', passengers=passengers)

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)

