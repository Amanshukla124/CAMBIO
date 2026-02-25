import sqlite3
import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask import jsonify, request


app = Flask(__name__)
app.secret_key = "supersecretkey"

# -----------------------------
# File Upload Config
# -----------------------------
UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


# -----------------------------
# Database Connection
# -----------------------------
def get_db_connection():
    conn = sqlite3.connect("database.db", timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


# -----------------------------
# Create Tables
# -----------------------------
def create_tables():
    conn = get_db_connection()

    # Users Table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            credits INTEGER DEFAULT 0
        )
    """)

    # Vouchers Table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS vouchers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            brand TEXT NOT NULL,
            value INTEGER NOT NULL,
            expiry TEXT NOT NULL,
            image TEXT,
            points INTEGER DEFAULT 0,
            tier TEXT DEFAULT 'Standard',
            status TEXT DEFAULT 'Pending',
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    # Transactions Table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            buyer_id INTEGER,
            seller_id INTEGER,
            voucher_id INTEGER,
            points INTEGER,
            timestamp TEXT,
            FOREIGN KEY(buyer_id) REFERENCES users(id),
            FOREIGN KEY(seller_id) REFERENCES users(id),
            FOREIGN KEY(voucher_id) REFERENCES vouchers(id)
        )
    """)

    conn.commit()
    conn.close()


create_tables()


# -----------------------------
# AI Rule-Based Engine
# -----------------------------
def calculate_points_and_tier(brand, value, expiry):
    base = int(value) * 0.5

    premium_brands = ["amazon", "apple", "nike", "flipkart"]
    gold_brands = ["zara", "puma", "myntra"]

    tier = "Standard"

    # Brand Boost
    if brand.lower() in premium_brands:
        base *= 1.5
        tier = "Premium"
    elif brand.lower() in gold_brands:
        base *= 1.2
        tier = "Gold"

    # Expiry Penalty
    expiry_date = datetime.strptime(expiry, "%Y-%m-%d")
    days_left = (expiry_date - datetime.now()).days

    if days_left < 30:
        base *= 0.7
        tier = "Basic"
    elif days_left < 60:
        base *= 0.85

    return int(base), tier


# -----------------------------
# Home
# -----------------------------
@app.route("/")
def home():
    return render_template("index.html")


# -----------------------------
# Signup
# -----------------------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        hashed_password = generate_password_hash(password)

        try:
            conn = get_db_connection()
            conn.execute(
                "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                (name, email, hashed_password)
            )
            conn.commit()
        except sqlite3.IntegrityError:
            return "Email already exists"
        finally:
            conn.close()

        return redirect(url_for("login"))

    return render_template("signup.html")


# -----------------------------
# Login
# -----------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()
        user = conn.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        ).fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            return redirect(url_for("dashboard"))

        return "Invalid Email or Password"

    return render_template("login.html")


# -----------------------------
# Dashboard
# -----------------------------
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()

    # Auto-expire vouchers
    conn.execute("""
        UPDATE vouchers
        SET status = 'Expired'
        WHERE status = 'Approved'
        AND date(expiry) < date('now')
    """)
    conn.commit()

    user = conn.execute(
        "SELECT * FROM users WHERE id = ?",
        (session["user_id"],)
    ).fetchone()

    vouchers = conn.execute(
        "SELECT * FROM vouchers WHERE user_id = ?",
        (session["user_id"],)
    ).fetchall()

    transactions = conn.execute("""
        SELECT * FROM transactions
        WHERE buyer_id = ? OR seller_id = ?
        ORDER BY timestamp DESC
    """, (session["user_id"], session["user_id"])).fetchall()

    conn.close()

    total_uploaded = len(vouchers)
    total_sold = len([v for v in vouchers if v["status"] == "Redeemed"])
    total_expired = len([v for v in vouchers if v["status"] == "Expired"])
    active_vouchers = len([v for v in vouchers if v["status"] == "Approved"])

    if total_uploaded > 0:
        redemption_rate = round((total_sold / total_uploaded) * 100)
        active_rate = round((active_vouchers / total_uploaded) * 100)
        expiry_rate = round((total_expired / total_uploaded) * 100)
    else:
        redemption_rate = 0
        active_rate = 0
        expiry_rate = 0

    return render_template(
        "dashboard.html",
        name=user["name"],
        credits=user["credits"],
        vouchers=vouchers,
        transactions=transactions,
        total_uploaded=total_uploaded,
        redemption_rate=redemption_rate,
        active_rate=active_rate,
        expiry_rate=expiry_rate
    )


# -----------------------------
# Upload Voucher
# -----------------------------
@app.route("/upload", methods=["GET", "POST"])
def upload():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        brand = request.form["brand"]
        value = request.form["value"]
        expiry = request.form["expiry"]
        image = request.files["image"]

        filename = None
        if image and image.filename != "":
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        points, tier = calculate_points_and_tier(brand, value, expiry)

        conn = get_db_connection()

        conn.execute("""
            INSERT INTO vouchers 
            (user_id, brand, value, expiry, image, points, tier, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (session["user_id"], brand, value, expiry, filename, points, tier, "Approved"))

        conn.execute(
            "UPDATE users SET credits = credits + ? WHERE id = ?",
            (points, session["user_id"])
        )

        conn.commit()
        conn.close()

        return redirect(url_for("dashboard"))

    return render_template("upload.html")


# -----------------------------
# Marketplace
# -----------------------------
@app.route("/marketplace")
def marketplace():
    if "user_id" not in session:
        return redirect(url_for("login"))

    search = request.args.get("search", "")
    tier_filter = request.args.get("tier", "")
    max_points = request.args.get("max_points", "")

    conn = get_db_connection()

    # Auto-expire vouchers
    conn.execute("""
        UPDATE vouchers
        SET status = 'Expired'
        WHERE status = 'Approved'
        AND date(expiry) < date('now')
    """)
    conn.commit()

    query = """
        SELECT vouchers.*, users.name 
        FROM vouchers
        JOIN users ON vouchers.user_id = users.id
        WHERE vouchers.status = 'Approved'
        AND vouchers.user_id != ?
    """
    params = [session["user_id"]]

    # Search by brand
    if search:
        query += " AND LOWER(vouchers.brand) LIKE ?"
        params.append(f"%{search.lower()}%")

    # Filter by tier
    if tier_filter:
        query += " AND vouchers.tier = ?"
        params.append(tier_filter)

    # Filter by max points
    if max_points:
        query += " AND vouchers.points <= ?"
        params.append(max_points)

    query += " ORDER BY vouchers.points ASC"

    vouchers = conn.execute(query, params).fetchall()

    conn.close()

    return render_template("marketplace.html", vouchers=vouchers)

# -----------------------------
# Redeem Voucher (Credit Transfer)
# -----------------------------
@app.route("/redeem/<int:voucher_id>")
def redeem(voucher_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()

    voucher = conn.execute(
        "SELECT * FROM vouchers WHERE id = ? AND status = 'Approved'",
        (voucher_id,)
    ).fetchone()

    buyer = conn.execute(
        "SELECT * FROM users WHERE id = ?",
        (session["user_id"],)
    ).fetchone()

    if not voucher:
        conn.close()
        return "Voucher not available"

    if buyer["credits"] < voucher["points"]:
        conn.close()
        return "Not enough credits"

    seller_id = voucher["user_id"]
    points = voucher["points"]

    # Deduct from buyer
    conn.execute(
        "UPDATE users SET credits = credits - ? WHERE id = ?",
        (points, buyer["id"])
    )

    # Transfer to seller
    conn.execute(
        "UPDATE users SET credits = credits + ? WHERE id = ?",
        (points, seller_id)
    )

    # Mark redeemed
    conn.execute(
        "UPDATE vouchers SET status = 'Redeemed' WHERE id = ?",
        (voucher_id,)
    )

    # Record transaction
    conn.execute("""
        INSERT INTO transactions 
        (buyer_id, seller_id, voucher_id, points, timestamp)
        VALUES (?, ?, ?, ?, ?)
    """, (
        buyer["id"],
        seller_id,
        voucher_id,
        points,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.commit()
    conn.close()

    return redirect(url_for("dashboard", success="true"))

@app.route("/calculate-points", methods=["POST"])
def calculate_points():

    data = request.json

    brand = data.get("brand", "")
    value = float(data.get("value", 0))
    expiry = data.get("expiry", "")
    category = data.get("category", "")

    # ---- Your AI rule logic ----
    points = 0
    tier = "Standard"

    if value >= 5000:
        tier = "Premium"
        points = int(value * 0.30)
    elif value >= 2000:
        tier = "Gold"
        points = int(value * 0.20)
    else:
        tier = "Standard"
        points = int(value * 0.10)

    return jsonify({
        "points": points,
        "tier": tier
    })
# -----------------------------
# Logout
# -----------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)
