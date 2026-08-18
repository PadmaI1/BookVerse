<p align="center">
  <img src="static/img/favicon.svg" alt="BookVerse logo" width="120">
</p>

<h1 align="center">BookVerse</h1>

<p align="center">
  <em>A lending library for your neighbourhood. Lend the books you love, borrow the ones you want.</em>
</p>

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/python-3.10+-7a2231?style=flat-square">
  <img alt="Flask" src="https://img.shields.io/badge/flask-3.1-7a2231?style=flat-square">
  <img alt="Payments" src="https://img.shields.io/badge/payments-Razorpay-d4a93e?style=flat-square">
</p>

---

## What it does

BookVerse lets readers in a community share their shelves. Owners list books they are happy to lend, borrowers send a request and pay a **refundable security deposit**, and the deposit goes back once the owner confirms the book is returned.

- **Discover** – browse the home feed, search, filter by city or availability, and sort by rating.
- **Explore genres** – every genre has its own themed page, with its own emoji, quote and mood.
- **Lend a book** – add a book with a cover (searchable through Unsplash), a rating and a deposit amount.
- **Borrow requests** – a clear request → approve → pay deposit → active → returned flow for both sides.
- **Secure deposits** – payments run through Razorpay with signature verification and automatic refunds on return.
- **Real-time chat** – owner and borrower talk about a specific book over Socket.IO.
- **Owner dashboard** – your shelf, incoming requests and loans in one place.
- **Profiles** – reader levels, badges, lending stats and a filterable shelf.
- **Notifications** – real read/unread state with links straight to what changed.
- **Accounts** – email verification, change password, edit profile, and safe account deletion.
- **Light and dark themes** – a burgundy "library" look that works at phone width too.

## Tech stack

| Area | Tools |
| --- | --- |
| Backend | Flask, Flask-SQLAlchemy, Flask-Migrate, Flask-Login, Flask-WTF |
| Real time | Flask-SocketIO |
| Payments | Razorpay |
| Email | Flask-Mail |
| Database | SQLite by default (any SQLAlchemy URL works) |
| Frontend | Jinja templates, one hand-written stylesheet, Lucide icons |

## Getting started

```bash
git clone https://github.com/PadmaI1/BookVerse.git
cd BookVerse
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill it in:

| Variable | Purpose |
| --- | --- |
| `SECRET_KEY` | Flask session and CSRF signing key |
| `SQLALCHEMY_DATABASE_URI` | e.g. `sqlite:///books.db` |
| `MAIL_USERNAME`, `MAIL_PASSWORD` | SMTP account (Gmail app password) used for verification emails |
| `BASE_URL` | Public address used in verification links |
| `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`, `RAZORPAY_WEBHOOK_SECRET` | Razorpay keys (use test mode while developing) |
| `UNSPLASH_ACCESS_KEY` | Book cover search |

Create the database, load demo data, and start the app:

```bash
flask --app app db upgrade
python scripts/seed_data.py
python app.py
```

Then open <http://127.0.0.1:5000>. The seed script creates a handful of demo readers, genres, books, requests and chats so every page has something to show.

## Tests

```bash
python -m unittest discover tests
```

## Project layout

```
app.py            application setup and error pages
models.py         User, Genre, Book, BorrowRequest, Message, Notification, Payment
forms.py          Flask-WTF forms
routes/           books, auth, users, dashboard and chat blueprints
payments.py       Razorpay order, verification and refund flow
socket_events.py  real-time chat events
templates/        Jinja pages, partials and the verification email
static/           stylesheet, banners, logo and uploads
scripts/          demo data seeding
tests/            unit tests
```

## Notes for deployment

- Turn off `debug=True` in `app.py` and serve behind a production server.
- Set `BASE_URL` to your real domain so verification links work.
- Use live Razorpay keys only on a site served over HTTPS.
