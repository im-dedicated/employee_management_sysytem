import os
import sqlite3
from functools import wraps

from flask import Flask, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "employee-management-secret-key")
app.config["DATABASE"] = os.path.join(app.root_path, "employees.db")


def get_db():
    if "db" not in g:
        conn = sqlite3.connect(app.config["DATABASE"])
        conn.row_factory = sqlite3.Row
        g.db = conn
    return g.db


@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT NOT NULL,
            department TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS help_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            subject TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """
    )
    db.commit()


with app.app_context():
    init_db()


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped_view


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not username or not email or not password:
            flash("All fields are required.", "danger")
            return redirect(url_for("register"))

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("register"))

        db = get_db()
        existing = db.execute(
            "SELECT id FROM users WHERE username = ? OR email = ?",
            (username, email),
        ).fetchone()
        if existing:
            flash("A user with that username or email already exists.", "danger")
            return redirect(url_for("register"))

        db.execute(
            "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
            (username, email, generate_password_hash(password)),
        )
        db.commit()
        flash("Registration successful! Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        db = get_db()
        user = db.execute(
            "SELECT id, username, password FROM users WHERE username = ?",
            (username,),
        ).fetchone()

        if user and check_password_hash(user["password"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            flash("Welcome back!", "success")
            return redirect(url_for("dashboard"))

        flash("Invalid username or password.", "danger")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))


@app.route("/dashboard")
@login_required
def dashboard():
    db = get_db()
    employees = db.execute(
        "SELECT * FROM employees WHERE user_id = ? ORDER BY created_at DESC",
        (session["user_id"],),
    ).fetchall()
    help_requests = db.execute(
        "SELECT * FROM help_requests WHERE user_id = ? ORDER BY created_at DESC",
        (session["user_id"],),
    ).fetchall()
    return render_template("dashboard.html", employees=employees, help_requests=help_requests)


@app.route("/employees", methods=["GET", "POST"])
@login_required
def employees():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        role = request.form.get("role", "").strip()
        department = request.form.get("department", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()

        if not all([full_name, role, department, email, phone]):
            flash("All employee fields are required.", "danger")
            return redirect(url_for("employees"))

        db = get_db()
        db.execute(
            "INSERT INTO employees (user_id, full_name, role, department, email, phone) VALUES (?, ?, ?, ?, ?, ?)",
            (session["user_id"], full_name, role, department, email, phone),
        )
        db.commit()
        flash("Employee added successfully.", "success")
        return redirect(url_for("dashboard"))

    return redirect(url_for("dashboard"))


@app.route("/employees/<int:employee_id>/edit", methods=["GET", "POST"])
@login_required
def edit_employee(employee_id):
    db = get_db()
    employee = db.execute(
        "SELECT * FROM employees WHERE id = ? AND user_id = ?",
        (employee_id, session["user_id"]),
    ).fetchone()

    if employee is None:
        flash("Employee not found.", "danger")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        role = request.form.get("role", "").strip()
        department = request.form.get("department", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()

        if not all([full_name, role, department, email, phone]):
            flash("All employee fields are required.", "danger")
            return redirect(url_for("edit_employee", employee_id=employee_id))

        db.execute(
            "UPDATE employees SET full_name = ?, role = ?, department = ?, email = ?, phone = ? WHERE id = ? AND user_id = ?",
            (full_name, role, department, email, phone, employee_id, session["user_id"]),
        )
        db.commit()
        flash("Employee updated successfully.", "success")
        return redirect(url_for("dashboard"))

    return render_template("edit_employee.html", employee=employee)


@app.route("/help", methods=["GET", "POST"])
@login_required
def help_desk():
    if request.method == "POST":
        subject = request.form.get("subject", "").strip()
        message = request.form.get("message", "").strip()

        if not subject or not message:
            flash("Please enter both a subject and your message.", "danger")
            return redirect(url_for("help_desk"))

        db = get_db()
        db.execute(
            "INSERT INTO help_requests (user_id, subject, message) VALUES (?, ?, ?)",
            (session["user_id"], subject, message),
        )
        db.commit()
        flash("Your help request has been submitted.", "success")
        return redirect(url_for("dashboard"))

    return render_template("help.html")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=os.environ.get("FLASK_DEBUG", "0") == "1", host="0.0.0.0", port=port)
