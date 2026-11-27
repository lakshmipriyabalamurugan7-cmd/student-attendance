
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
import mysql.connector

app = Flask(__name__)
CORS(app)


# MySQL Database Connection
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Priya@2026",
        database="student_attendance"
    )


# Serve Frontend
@app.route("/")
def home():
    return send_file("../frontend/index.html")


# Login API
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}

    role = data.get("role", "").strip().lower()
    name = data.get("name", "").strip()
    email = data.get("email", "").strip()
    password = data.get("password", "")

    # Admin requires all fields
    if role == "admin" and (not name or not email or not password):
        return jsonify({
            "message": "Please enter name, email and password"
        }), 400

    # Faculty requires only name
    if role == "faculty" and not name:
        return jsonify({
            "message": "Please enter faculty name"
        }), 400

    # Student requires all fields
    if role == "student" and (not name or not email or not password):
        return jsonify({
            "message": "Please enter name, email and password"
        }), 400

    db = None
    cursor = None

    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        # ADMIN LOGIN - Verify existing credentials
        if role == "admin":
            cursor.execute(
                """
                SELECT * FROM admin
                WHERE name=%s AND email=%s AND password=%s
                """,
                (name, email, password)
            )

            user = cursor.fetchone()

            if user:
                return jsonify({
                    "message": "Login successful!",
                    "role": "admin",
                    "name": user["name"],
                    "email": user["email"]
                }), 200

            return jsonify({
                "message": "Invalid name, email or password"
            }), 401

        # FACULTY LOGIN - Any name can login
        elif role == "faculty":
            cursor.execute(
                "SELECT * FROM faculty WHERE name=%s",
                (name,)
            )
            user = cursor.fetchone()

            if not user:
                cursor.execute(
                    "INSERT INTO faculty (name) VALUES (%s)",
                    (name,)
                )
                db.commit()

            return jsonify({
                "message": "Login successful!",
                "role": "faculty",
                "name": name,
                "email": email
            }), 200

        # STUDENT LOGIN - Any name, email and password can login
        elif role == "student":
            cursor.execute(
                "SELECT * FROM students WHERE email=%s",
                (email,)
            )
            user = cursor.fetchone()

            if user:
                # Update existing student details
                cursor.execute(
                    """
                    UPDATE students
                    SET name=%s, password=%s
                    WHERE email=%s
                    """,
                    (name, password, email)
                )
                db.commit()
            else:
                # Save new student
                cursor.execute(
                    """
                    INSERT INTO students (name, email, password)
                    VALUES (%s, %s, %s)
                    """,
                    (name, email, password)
                )
                db.commit()

            return jsonify({
                "message": "Login successful!",
                "role": "student",
                "name": name,
                "email": email
            }), 200

        else:
            return jsonify({
                "message": "Invalid role"
            }), 400

    except Exception as e:
        return jsonify({
            "message": "Database error: " + str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()


if __name__ == "__main__":
    app.run(debug=True, port=5000)
