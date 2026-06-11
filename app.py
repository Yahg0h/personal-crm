import os
import sqlite3
from flask import Flask, flash, redirect, render_template, request, session, jsonify
from flask_session import Session
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, date
from dotenv import load_dotenv


from helpers import login_required, save_file

# Configure application
app = Flask(__name__)
load_dotenv()
app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY")
csrf = CSRFProtect(app)
limiter = Limiter(key_func=lambda: request.remote_addr, app=app)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure SQLite database (row_factory is important to acess files by name instead of index)
def get_db():
    conn = sqlite3.connect('crm.db')
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute") # Max of 5 tries/requests per mintue to log in
def login():
    session.clear()
    # Get user inputs and verify if they aren't empty
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username:
            flash("Username is required.")
            return render_template("login.html")

        if not password:
            flash("Password is required.")
            return render_template("login.html")
        # Verify if username and password are correct or exist
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        db.close()

        if not user or not check_password_hash(user["password_hash"], password):
            flash("Invalid username and/or password.")
            return render_template("login.html")
        # If all well, log user in
        session["user_id"] = user["id"]

        return redirect("/")
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    # Clear the user current session and log them off
    session.clear()
    flash("You have been logged out.")
    return redirect("/login")

@app.route("/register", methods=["GET", "POST"])
@limiter.limit("5 per minute") # Max of 5 tries/requests per mintue to sign up
def register():
    # Get user inputs and verify if they aren't empty
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirm_password = request.form.get("confirmation")

        if not username:
            flash("Username is required.")
            return render_template("register.html")

        if not password or not confirm_password:
            flash("Password is required.")
            return render_template("register.html")

        # Verify if the password was inputted correctly twice
        if password != confirm_password:
            flash("Passwords do not match.")
            return render_template("register.html")

        # Verify if chosen username already exists, if yes, don't register the user
        db = get_db()
        existing_username = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        if existing_username:
            flash("Username already exists.")
            return render_template("register.html")

        # Hash password to make it secure and add new user to the database
        hashed_password = generate_password_hash(password)
        db.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, hashed_password))
        db.commit()

        # Insert default categories for the new user
        user = db.execute("SELECT last_insert_rowid() AS id").fetchone()
        default_categories = ["Family", "Friends", "Work", "Others"]
        for category_name in default_categories:
            db.execute("INSERT INTO categories (user_id, name) VALUES (?, ?)", (user["id"], category_name))
        db.commit()
        db.close()

        # Registration finished, redirect them to log in
        flash("Registration successful! Please log in.")
        return redirect("/login")

    else:
        return render_template("register.html")

@app.route("/")
@login_required
def index():
        # Get all necessary info from database for the dashboard and pass it to the template (dashboard.html)
        # Info means: Recent alert_after_days, birthday celebrants of the month and the 5 most recent interactions registered by the user.
        user = session["user_id"]
        db = get_db()
        # This SQL query (alerts) was made with the help of artificial intelligence (Claude).
        alerts = db.execute("""
            SELECT c.id, c.name, c.photo_path, c.alert_after_days,
                MAX(i.interaction_date) as last_contact,
                CAST(julianday('now') - julianday(MAX(i.interaction_date)) AS INTEGER) AS days_ago
            FROM contacts c
            LEFT JOIN interactions i ON c.id = i.contact_id
            WHERE c.user_id = ?
            GROUP BY c.id
            HAVING last_contact IS NOT NULL AND CAST(julianday('now') - julianday(last_contact) AS INTEGER) >= c.alert_after_days
            ORDER BY days_ago DESC
        """, (user,)).fetchall()

        monthly_birthdays = db.execute("SELECT * FROM contacts WHERE user_id = ? AND strftime('%m', birthday) = strftime('%m', 'now') ORDER BY strftime('%d', birthday)", (user,)).fetchall()
        recent_interactions = db.execute("SELECT i.*, c.name as contact_name FROM interactions i JOIN contacts c ON i.contact_id = c.id WHERE i.user_id = ? ORDER BY i.interaction_date DESC LIMIT 5", (user,)).fetchall()
        db.close()

        # Return info to be displayed at the dashboard
        return render_template("dashboard.html", alerts=alerts, monthly_birthdays=monthly_birthdays, recent_interactions=recent_interactions)

@app.route("/contacts/new", methods=["GET", "POST"])
@login_required
def new_contact():
    if request.method == "POST":
        # Get all user input from form
        name = request.form.get("name")
        nickname = request.form.get("nickname")
        phone = request.form.get("phone")
        email = request.form.get("email")
        birthday = request.form.get("birthday")
        notes = request.form.get("notes")
        category_id = request.form.get("category")

        # Get categories for dropdown (+ user id for queries)
        user = session["user_id"]
        db = get_db()
        categories = db.execute("SELECT * FROM categories WHERE user_id = ?", (user,)).fetchall()
        db.close()

        # Verify that all required fields are filled
        if not name or not category_id:
            flash("Name and category fields are required.")
            return render_template("contact_form.html", categories=categories)

        # Validate birthday format (if there's one)
        birthday_date = None
        if birthday:
            try:
                birthday_date = datetime.strptime(birthday, "%Y-%m-%d").date()
                # Stop user from inputting a birthday way above todays date
                if birthday_date > date.today():
                    flash("Birthday cannot be in the future.")
                    return render_template("contact_form.html", categories=categories)
            except ValueError:
                flash("Invalid birthday format. Please use YYYY-MM-DD.")
                return render_template("contact_form.html", categories=categories)

        # Handle contact picture upload, add its location to db's photo_path
        photo_url = None
        if "photo" in request.files and request.files["photo"].filename != "":
            try:
                photo_url = save_file(request.files["photo"], "static/uploads/photos")
            except ValueError as e:
                flash(str(e))
                return render_template("contact_form.html", categories=categories)

        # Add contact to database
        db = get_db()
        db.execute("INSERT INTO contacts (user_id, category_id, name, nickname, phone, email, birthday, photo_path, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (user, category_id, name, nickname, phone, email, birthday_date, photo_url, notes))
        db.commit()
        db.close()

        # Redirect
        flash("Contact added successfully!")
        return redirect("/contacts")
    else:
        # Get categories for dropdown (+ user id for queries)
        user = session["user_id"]
        db = get_db()
        categories = db.execute("SELECT * FROM categories WHERE user_id = ?", (user,)).fetchall()
        db.close()

        # Return to contact and pass categories for the dropdown
        return render_template("contact_form.html", categories=categories)

@app.route("/contacts")
@login_required
def contacts():
    # Get all user inputs from form
    user = session["user_id"]
    category_id = request.args.get("category_id")
    sort = request.args.get("sort")
    db = get_db()
    # This SQL query (select_query) was made with the help of artificial intelligence (Claude).
    select_query = """
        SELECT c.id, c.name, c.category_id, cat.name as category_name,
            MAX(i.interaction_date) as last_contact,
                            CAST(julianday('now') - julianday(COALESCE(MAX(i.interaction_date), date('now'))) AS INTEGER) AS days_ago
        FROM contacts c
        LEFT JOIN categories cat ON c.category_id = cat.id
        LEFT JOIN interactions i ON c.id = i.contact_id
    """

    # Define the order by based on chosen sort
    if sort == "name_desc":
        order_by = "ORDER BY LOWER(c.name) DESC"
    elif sort == "days_asc":
        order_by = "ORDER BY days_ago ASC"
    elif sort == "days_desc":
        order_by = "ORDER BY days_ago DESC"
    else:
        order_by = "ORDER BY LOWER(c.name) ASC"

    # Add category_id to filter if requested, if not, then don't
    if category_id:
        contacts = db.execute(select_query + " WHERE c.user_id = ? AND c.category_id = ? GROUP BY c.id " + order_by, (user, category_id)).fetchall()
    else:
        contacts = db.execute(select_query + " WHERE c.user_id = ? GROUP BY c.id " + order_by, (user,)).fetchall()

    # Get all categories owned by the user
    categories = db.execute("SELECT * FROM categories WHERE user_id = ?", (user,)).fetchall()
    db.close()

    # Return contacts and categories to contacts.html for filtering and sorting contacts
    return render_template("contacts.html", contacts=contacts, categories=categories)

@app.route("/contacts/<int:id>/edit", methods=["GET", "POST"])
@login_required
def edit_contact(id):
    user_id = session["user_id"]
    if request.method == "POST":
        # Get user input from form
        name = request.form.get("name")
        nickname = request.form.get("nickname")
        phone = request.form.get("phone")
        email = request.form.get("email")
        birthday = request.form.get("birthday")
        notes = request.form.get("notes")
        category_id = request.form.get("category")
        alert_after_days = request.form.get("alert_after_days")

        # Get categories for dropdown (+ user id for queries)
        user = session["user_id"]
        db = get_db()
        categories = db.execute("SELECT * FROM categories WHERE user_id = ?", (user,)).fetchall()
        db.close()

        # Verify that all required fields are filled
        if not name or not category_id:
            flash("Name and category fields are required.")
            return render_template("contact_form.html", categories=categories)

        # Validate birthday format (if there's one)
        birthday_date = None
        if birthday:
            try:
                birthday_date = datetime.strptime(birthday, "%Y-%m-%d").date()
            except ValueError:
                flash("Invalid birthday format. Please use YYYY-MM-DD.")
                return render_template("contact_form.html", categories=categories)

        # Get current contact to preserve photo if no new one is uploaded
        db = get_db()
        current_contact = db.execute("SELECT photo_path FROM contacts WHERE id = ?", (id,)).fetchone()
        db.close()
        contact_old_photo = current_contact["photo_path"] if current_contact else None

        # Handle contact picture upload/deletion in case of photo change
        photo_url = contact_old_photo
        if "photo" in request.files and request.files["photo"].filename != "":
            try:
                # Delete the old contact profile photo (if it exists)
                if contact_old_photo:
                    photo_file = contact_old_photo.replace('/static/uploads/photos/', '')
                    old_photo_path = os.path.join('static/uploads/photos', photo_file)
                    if os.path.exists(old_photo_path):
                        os.remove(old_photo_path)

                # Save the new photo
                photo_url = save_file(request.files["photo"], "static/uploads/photos")
            except ValueError as e:
                flash(str(e))
                return render_template("contact_form.html", categories=categories)

        # Check if the input in alert after days is a positive integer
        try:
           alert_after_days = int(alert_after_days)
           if alert_after_days <= 0:
               flash("Alert time must be positive integer.")
               return render_template("contact_form.html", categories=categories)
        except ValueError:
            flash("Invalid input. Insert an integer for your alert time.")
            return render_template("contact_form.html", categories=categories)

        # Update db
        db = get_db()
        db.execute("UPDATE contacts SET name = ?, nickname = ?, phone = ?, email = ?, birthday = ?, photo_path = ?, notes = ?, alert_after_days = ? , category_id = ? WHERE id = ? AND user_id = ?", (name, nickname, phone, email, birthday_date, photo_url, notes, alert_after_days, category_id, id, user_id))
        db.commit()
        db.close()

        # Redirect
        flash("Contact updated successfully!")
        return redirect("/contacts")

    else:
        # Get contact info from db
        db = get_db()
        contact = db.execute("SELECT * FROM contacts WHERE id = ? AND user_id = ?", (id, user_id)).fetchone()
        db.close()

        # Check if contact exists and belongs to user
        if not contact:
            flash("Contact not found.")
            return redirect("/contacts")

        # Get categories for dropdown
        db = get_db()
        categories = db.execute("SELECT * FROM categories WHERE user_id = ?", (user_id,)).fetchall()
        db.close()

        # Pass contact info to template and render form
        return render_template("contact_form.html", contact=contact, categories=categories)

@app.route("/contacts/<int:id>/delete", methods=["POST"])
@login_required
def delete_contact(id):
    user_id = session["user_id"]
    # Verify if the contact do be deleted is in the users contacts list or if it exists
    db = get_db()
    contact = db.execute("SELECT * FROM contacts WHERE id = ? AND user_id = ?", (id, user_id)).fetchone()
    if not contact:
        flash("Contact not found.")
        return redirect("/contacts")

    # If it exists (both the contact and a respective profile photo), delete the contact profile photo
    if contact["photo_path"]:
        photo_file = contact["photo_path"].replace('/static/uploads/photos/', '')
        photo_path = os.path.join('static/uploads/photos', photo_file)
        if os.path.exists(photo_path):
            os.remove(photo_path)

    # If it exists and it is in the users contacts list, delete it from users contacts list.
    db.execute("DELETE FROM contacts WHERE id = ? AND user_id = ?", (id, user_id))
    db.commit()
    db.close()

    # Redirect
    flash("Contact successfully deleted!")
    return redirect("/contacts")

@app.route("/contacts/<int:id>")
@login_required
def contact_detail(id):
    user_id = session["user_id"]
    # Get all selected contact info from the database to display on contact_detail.html
    db = get_db()
    contact = db.execute("""
        SELECT c.*, cat.name as category_name
        FROM contacts c
        LEFT JOIN categories cat ON c.category_id = cat.id
        WHERE c.id = ? AND c.user_id = ?
    """, (id, user_id)).fetchone()

    # If contact doesn't exist tell user and redirect
    if not contact:
        db.close()
        flash("Contact not found.")
        return redirect("/contacts")

    # Get all registered interactions between the contact and the user
    interactions = db.execute("SELECT * FROM interactions WHERE contact_id = ? AND user_id = ? ORDER BY interaction_date DESC", (id, user_id)).fetchall()
    db.close()

    # Return contact info and interactions historic to be displayed in contact_detail.html
    return render_template("contact_detail.html", contact=contact, interactions=interactions)

@app.route("/contacts/<int:id>/interactions", methods=["POST"])
@login_required
def add_interaction(id):
    user_id = session["user_id"]
    # Get data from form
    interaction_type = request.form.get("type")
    interaction_date = request.form.get("interaction_date")
    summary = request.form.get("summary")

    # Verify that all required fields are filled
    if not interaction_type or not interaction_date or not summary:
        flash("All fields are required.")
        return redirect(f"/contacts/{id}")

    # Validate date format
    try:
        interaction_date = datetime.strptime(interaction_date, "%Y-%m-%d").date()
    except ValueError:
        flash("Invalid date format. Please use YYYY-MM-DD.")
        return redirect(f"/contacts/{id}")

    # Insert into db
    db = get_db()
    db.execute("INSERT INTO interactions (type, interaction_date, summary, contact_id, user_id) VALUES (?, ?, ?, ?, ?)", (interaction_type, interaction_date, summary, id, user_id))
    db.commit()
    db.close()

    # Redirect
    flash("Interaction added successfully!")
    return redirect(f"/contacts/{id}")

@app.route("/interactions/<int:id>/delete", methods=["POST"])
@login_required
def delete_interaction(id):
    user_id = session["user_id"]
    # Check if interaction exists and belongs to user, if not, tell user and redirect
    db = get_db()
    interaction = db.execute("SELECT * FROM interactions WHERE id = ? AND user_id = ?", (id, user_id)).fetchone()
    if not interaction:
        flash("Interaction not found.")
        return redirect("/contacts")

    # If yes, delete the interaction
    db.execute("DELETE FROM interactions WHERE id = ? AND user_id = ?", (id, user_id))
    db.commit()
    db.close()

    # Redirect back to contact page
    flash("Interaction successfully deleted!")
    return redirect(f"/contacts/{interaction['contact_id']}")

@app.route("/api/contacts")
@login_required
def search_contacts():
    user = session["user_id"]
    # Get the query the user's typing into the contacts search box
    query = request.args.get("q")
    # If nothing typed or the user wasn't found, then return a empty json
    if not query:
        return jsonify([])

    # Look for the possible contacts searched on the query
    db = get_db()
    results = db.execute("SELECT id, name, category_id FROM contacts WHERE name LIKE ? AND user_id = ?", (f"%{query}%", user)).fetchall()
    db.close()

    # If found, get the contact and return json to contacts.html to display the option/results
    results = [dict(row) for row in results]
    return jsonify(results)

@app.route("/categories", methods=["GET", "POST"])
@login_required
def config_categories():
    if request.method == "POST":
        user = session["user_id"]
        # Get the name of the new category user wants to created
        custom_category = request.form.get("category_name")

        # Verify if there is input
        if not custom_category:
            flash("Custom category name is required.")
            return redirect("/categories")

        # If there is, add category to categories database
        db = get_db()
        db.execute("INSERT INTO categories (user_id, name) VALUES (?,?)", (user, custom_category))
        db.commit()
        db.close()

        # Redirect
        flash("Custom Category added successfully!")
        return redirect("/categories")
    else:
        user = session["user_id"]
        # Get all categories user has stored and display them in categories.html
        db = get_db()
        categories = db.execute("SELECT * FROM categories WHERE user_id = ?", (user,)).fetchall()
        db.close()

        # Return info to be displayed at categories
        return render_template("categories.html", categories=categories)

@app.route("/categories/<int:id>/delete", methods=["POST"])
@login_required
def delete_category(id):
    user = session["user_id"]
    # Verify if the category user wants to delete is owned by them in database
    db = get_db()
    category = db.execute("SELECT * FROM categories WHERE user_id = ? AND id = ?", (user, id)).fetchone()

    # If not found or not owned, tell the user and redirect
    if not category:
        flash("Category not found.")
        return redirect("/categories")

    # Check if there are any contacts with said category, if yes, don't delete category until its safe (no contact is under it)
    # This SQL query (count) was made with the help of artificial intelligence (Claude).
    count = db.execute("SELECT COUNT(*) as cnt FROM contacts WHERE category_id = ? AND user_id = ?", (id,user)).fetchone()['cnt']
    if count > 0:
        flash(f"Cannot delete category as it has {count} contacts using it. Move those contacts to another category first.")
        return redirect("/categories")

    # If found and owned, delete the category from the database
    db.execute("DELETE FROM categories WHERE user_id = ? AND id = ?", (user, id))
    db.commit()
    db.close()

    # Redirect
    flash("Category successfully deleted!")
    return redirect("/categories")

@app.errorhandler(404)
def not_found(error):
    return render_template("404_page.html"), 404

@app.errorhandler(500)
def server_error(error):
    return render_template("404_page.html"), 500

@app.errorhandler(429)
def too_many_requests(error):
    return render_template("429_page.html"), 429
