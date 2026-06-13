# Personal CRM - pCRM
#### Video Demo: [Personal CRM - pCRM (Showcase)](https://youtu.be/F9O7Sv0gkVU)
#### Description: A contact relationship management system where you can add contacts and record your latest interactions with them. The web application sends reminders of important dates and alerts so you can reconnect with your contacts after a certain period. Ideal for those with busy schedules who often forget to interact with their contacts regularly.

## What Personal CRM is?

**Personal CRM** _(Personal Contact Relationship Management or pCRM)_ is a web application I have built as my final project for [CS50x](https://cs50.harvard.edu/x/). The idea for this project came from a common problem that happens to me and I know happens to other people as well, the fact that I forget to interact and talk to my friends and acquaintances because of the craziness of everyday life, either a lot of tasks or other things that take up your time. Even though social media exists and you can see photos and some of the things they're doing, it's not the same as talking to them, listening to them, or even seeing them, whether in person or on a Discord call, because it's in moments like these that I created a good portion of the fond memories I cherish. So, based on the original CRM _(Customer Relationship Management)_ tool, that is something companies use to track relationships with clients, I decided this type of thing would be amazing to help with this goal of trying to make you get more connected (or remember easily) to get in touch with your friends, family and more!

This app lets you manage a list of contacts — friends, family, coworkers and more (custom) — and track your interactions with them. You can log calls, messages, meetings, and more. The app will alert you when you haven't been in touch with someone for too long, and it shows you whose birthday is coming up this month. The goal is to make it easier to be intentional and in a real cool connection with the relationships you care about.

> This is an updated version of the original project submitted to CS50x, with the only changes made to polish the application's appearance (UI/Front-end).

## Features
 
- 👥 **Contact Management** - Create, read, update, and delete contacts with detailed information
- 📅 **Interaction Tracking** - Log calls, messages, meetings, video calls, and more
- 🔔 **Smart Alerts** - Get notified when you haven't contacted someone for a customizable period
- 🎂 **Birthday Reminders** - Never miss a birthday with automatic monthly birthday alerts
- 🏷️ **Custom Categories** - Organize contacts by your own custom categories (Friends, Family, Work, etc)
- 🔍 **Real-time Search** - Quickly find contacts with instant AJAX-powered search
- 📸 **Profile Photos** - Upload and manage profile pictures for your contacts
- 📊 **Dashboard Overview** - View alerts, upcoming birthdays, and recent interactions at a glance
- 🔐 **Secure Authentication** - Password hashing and user isolation
- ⚡ **Rate Limiting** - Protected against brute force login attempts
- 🛡️ **CSRF Protection** - Secure form submissions with tokens

### Tech Stack

For this project I used the following technologies:

| Layer      | Technology                        |
| ---------- | --------------------------------- |
| Backend    | Python, Flask, Flask-Session, Flask-wtf, Flask-limiter      |
| Database   | SQLite                            |
| Frontend   | HTML, CSS, JavaScript, Bootstrap 5|
| Other      | Werkzeug, Pillow, python-dotenv   |

---

## Files and Structure

### `app.py`

This is heart of pCRM that connects everything togheter and makes everything work. Contains all Flask routes and their logic.

- **Authentication routes** (`/login`, `/logout`, `/register`): Handle user registration and login using hashed passwords via `werkzeug`. On registration, four default categories (`Family`, `Friends`, `Work`, `Others`) are automatically created for the new user.
- **Dashboard** (`/`): The home page after login. Runs three queries to populate three sections: contacts overdue for a check-in (alerts), contacts with birthdays this month, and the five most recent interactions.
- **Contacts** (`/contacts`): Lists all contacts for the logged-in user. Supports filtering by category and sorting by name (A-Z, Z-A) or by days since last contact. Sorting is case-insensitive using SQLite's `LOWER()` function.
- **Contact detail** (`/contacts/<id>`): Shows full information about a single contact, including their interaction history. Joins the `categories` table to display the category name.
- **Add/Edit contact** (`/contacts/new`, `/contacts/<id>/edit`): Shared form (`contact_form.html`) used for both creating and editing contacts. Handles optional photo uploads, birthday date validation, and — on edit — the `alert_after_days` field. On edit, the existing photo is preserved if no new one is uploaded.
- **Delete contact** (`/contacts/<id>/delete`): Deletes a contact. Uses a `user_id` check to ensure users can only delete their own contacts.
- **Interactions** (`/contacts/<id>/interactions`, `/interactions/<id>/delete`): Allows adding and deleting interaction records associated with a contact.
- **Search API** (`/api/contacts`): A JSON endpoint consumed by the real-time search on the contacts page. Uses a `LIKE` query with wildcard matching and returns results as a JSON array.
- **Categories** (`/categories`, `/categories/<id>/delete`): Allows users to create and delete custom categories for organizing contacts.
- **Error handlers**: Custom `404`, `500` and `429` error pages to handle unexpected navigation gracefully.

### `helpers.py`

Contains utility functions used across the application.

- `login_required`: A decorator that redirects unauthenticated users to `/login`. Applied to all routes that require a session.
- `allowed_file`: Validates that an uploaded file has an accepted extension (`png`, `jpg`, `jpeg`, `webp`).
- `save_file`: Handles the actual photo upload process — validates the file, generates a unique filename using `uuid.uuid4()` to avoid collisions, saves it to disk, and returns a URL-friendly path for storage in the database.

### `crm.db`/`schema.sql`

Here is a description of all the tables in the SQLite database, which is composed of 4 tables:

| Table          | Description                                                                 |
| -------------- | --------------------------------------------------------------------------- |
| `users`        | Stores usernames and hashed passwords                                       |
| `contacts`     | Stores contact info, optional fields, and `alert_after_days`               |
| `categories`   | Stores categories per user, pre-populated with defaults on registration     |
| `interactions` | Stores interaction records (type, date, summary) linked to a contact        |

> Foreign keys are enforced with `ON DELETE CASCADE` and `ON DELETE SET NULL` where appropriate.

### `templates/`

All HTML templates extend `layout.html` (they use `layout.html` as a base which they build on), which contains the Bootstrap navbar, flash message display, and shared structure.

- `layout.html`: Base template. Conditionally shows different navbar links depending on whether the user is logged in. Loads Bootstrap 5, Bootstrap Icons, and a custom stylesheet.
- `login.html` / `register.html`: Authentication forms. The registration page includes client-side JavaScript to validate that both password fields match before submitting.
- `dashboard.html`: Three-section layout — alerts, upcoming birthdays, and recent interactions. Alerts and birthdays use horizontal scrolling card rows.
- `contacts.html`: A filterable, sortable contacts table with real-time search powered by a JavaScript `fetch` call to the `/api/contacts` endpoint.
- `contact_form.html`: Shared form for adding and editing contacts. Uses Jinja2 conditionals to pre-fill fields when editing and to show the `alert_after_days` field only during edits.
- `contact_detail.html`: Displays full contact information alongside an interaction log. Includes a collapsible form (Bootstrap's collapse component) for adding new interactions.
- `categories.html`: A compact page to add and delete custom categories, with a scrollable list of existing ones.
- `404_page.html`: Custom error page shown for `404` and `500` errors.
- `429_page.html`: Custom error page shown for `429` error.

### `static/`

Contains the custom stylesheet (`styles.css`), the favicon, a default profile picture (`def-pic.jpg`) used when a contact has no photo, and the `uploads/photos/` folder where contact photos are stored.

### `requirements.txt`

Here are the requirements for the application to function:

```
flask
flask_session
flask-wtf
flask-limiter
python-dotenv
Pillow
werkzeug
```

---

## Security Features
 
This application implements several security best practices:
 
- **Password Hashing**: User passwords are hashed using Werkzeug's `generate_password_hash()`
- **SQL Injection Prevention**: All database queries use prepared statements with placeholders
- **XSS Protection**: HTML is automatically escaped by Jinja2 templates
- **CSRF Protection**: Forms are protected with Flask-WTF CSRF tokens
- **Rate Limiting**: Login/Register endpoint limited to 5 attempts per minute
- **User Isolation**: Users can only access their own contacts and data
- **File Upload Validation**: Photo uploads are validated by type and size (5MB max)
---
 
## Quick Start
 
1. Clone the repository
```bash
git clone https://github.com/Yahg0h/personal-crm.git
cd personal-crm
```
 
2. Install dependencies
```bash
pip install -r requirements.txt
```
 
3. Initialize database
```bash
python3 -c "import sqlite3; sqlite3.connect('crm.db').executescript(open('schema.sql').read())"
```
 
4. Create `.env` file with your secret key
```bash
echo "FLASK_SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')" > .env
```
> **It is required to create a .env file with a secret key created by you for the application to function;** otherwise, you will receive `RuntimeError: A secret key is required to use CSRF.` in your terminal and an error page on the application.

5. Run the application
```bash
python -m flask run
```
 
6. Open the created server in your browser
7. Create an account and start adding contacts!
---

## Design Choices

### Why is the front-end design so simple?

I chose a simpler design because I really enjoyed learning and found myself more drawn to backend development during the duration of CS50x. Having a very basic, straightforward UI made it much easier for me to understand and see the backend changes I was implementing. Even though it's simple, it's functional, which I consider a fair trade-off.

Unlike the version of the project submitted to CS50x, Google Antigravity was used in this one to polish the frontend visual elements, adding subtle micro-interactions while preserving the simple, functional aspect. I chose to style the interface based on the old 2018 Roblox layout because I have always been a fan of that simplistic but functional style, which fitted perfectly with the exact look I had when making the frontend originally for CS50 which I decided to add here in this version.

### SQLite over MySQL

Early in planning, I considered using MySQL for the database. But later I decided to use SQLite for its simplicity, since the database is a single, very simple file. So, for this situation, I decided that SQLite was the best option for me, also because I am already more familiar with it.

### Add and edit using the same form template.

Instead of creating two different HTML files to add and edit contacts, I edited the `contact_form.html` file so that it could change the text and usage in both cases, using the Jinja conditionals I learned in the course. I think it was worthwhile, as it avoids creating two practically identical .html files to do essentially the same thing.

### UUID for photo filenames

Since I wanted users to be able to upload profile pictures for their contacts, I didn't want the database to have errors due to two contacts having the same name for a `photo.jpg` file, for example. So, I did some research and discovered the `uuid.uuid4()` function, which helps store photos with a new, unique name for each one, instead of keeping the original filename. This worked well because it avoided potential filename conflicts (two users uploading `photo.jpg`), and it's also good for privacy, since some photos have names that show the creation date and may contain metadata. This also helps in that aspect and makes managing the static file directory easier, as there will be no duplicate names.

---
 
## License
 
This project is licensed under the MIT License.
 
## Author
 
Made by [Yahgoh](https://github.com/Yahg0h) (that's me!). Hope you guys enjoy.