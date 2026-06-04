# 🏫 CampusStock — Cloud-Based Campus Inventory Management System

A full-stack web application built with **Flask + Firebase Firestore** for managing educational institution assets — computers, lab equipment, furniture, and more.

---

## ✨ Features

### Core
- 🔐 **User Authentication** — Admin & Staff roles with session management
- 📦 **CRUD Inventory** — Add, view, edit, delete items
- 🔍 **Search & Filter** — By name, category, department, status
- 📊 **Analytics Dashboard** — Charts for category, status, department distribution
- ☁️ **Firebase Firestore** — Real-time cloud database (with in-memory fallback for demo)

### Advanced
- 📱 **QR Code Generation** — Per-item QR codes, downloadable as PNG
- 👤 **Role-Based Access** — Admin: full CRUD; Staff: view/update only
- ⚠️ **Low Stock Alerts** — Visual alerts when quantity ≤ threshold
- 📋 **Activity Logs** — Timestamped log of add/update/delete actions
- 📄 **Reports** — Stock summary, progress bars, CSV export, print view

---

## 🚀 Quick Start

### 1. Clone & Setup

```bash
git clone <your-repo>
cd campus_inventory
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Firebase Setup (Optional — app works without it)

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Create a project → Firestore Database → Start in test mode
3. Project Settings → Service Accounts → Generate new private key
4. Save as `serviceAccountKey.json` in the project root

### 3. Environment

```bash
cp .env.example .env
# Edit .env if needed
```

### 4. Run

```bash
python app.py
```

Open **http://localhost:5000**

---

## 🔑 Demo Credentials

| Role  | Email              | Password  |
|-------|--------------------|-----------|
| Admin | admin@campus.edu   | admin123  |
| Staff | staff@campus.edu   | staff123  |

---

## 📁 Project Structure

```
campus_inventory/
├── app.py                  # Flask application (routes, API, DB logic)
├── requirements.txt
├── .env.example
├── serviceAccountKey.json  # ← Your Firebase key (DO NOT commit this)
└── templates/
    ├── base.html           # Shared layout (sidebar, nav, toast, modals)
    ├── login.html          # Login page
    ├── dashboard.html      # Analytics dashboard
    ├── inventory.html      # CRUD inventory table
    ├── reports.html        # Reports + CSV export
    └── logs.html           # Activity log
```

---

## 🗄️ Database Schema

### Collection: `inventory`
| Field       | Type   | Description                        |
|-------------|--------|------------------------------------|
| id          | string | Document ID (e.g. ITEM001)         |
| name        | string | Item name                          |
| category    | string | Electronics / Furniture / etc.     |
| quantity    | number | Current stock                      |
| department  | string | Owning department                  |
| status      | string | Available / In Use / Damaged       |
| threshold   | number | Low-stock alert level              |
| created_at  | string | Date added (YYYY-MM-DD)            |
| updated_at  | string | Last updated (YYYY-MM-DD)          |

### Collection: `activity_logs`
| Field      | Type   |
|------------|--------|
| action     | string | ADD / UPDATE / DELETE
| item_id    | string |
| item_name  | string |
| user       | string | email of actor
| timestamp  | string | YYYY-MM-DD HH:MM:SS

---

## 🌐 API Endpoints

| Method | Endpoint           | Description              | Auth   |
|--------|--------------------|--------------------------|--------|
| POST   | /login             | Authenticate user        | Public |
| GET    | /api/items         | List items (filterable)  | Any    |
| POST   | /api/items         | Create item              | Admin  |
| GET    | /api/items/:id     | Get single item          | Any    |
| PUT    | /api/items/:id     | Update item              | Any    |
| DELETE | /api/items/:id     | Delete item              | Admin  |
| GET    | /api/stats         | Dashboard statistics     | Any    |
| GET    | /api/qr/:id        | Generate QR code         | Any    |
| GET    | /api/logs          | Activity logs            | Any    |

---

## 🚢 Deployment (Render / Railway / Fly.io)

1. Push to GitHub
2. Set environment variables:
   - `SECRET_KEY` = random string
   - `FIREBASE_CREDENTIALS` = paste contents of `serviceAccountKey.json`
3. Start command: `gunicorn app:app`

---

## 🛡️ Security Notes

- Add `serviceAccountKey.json` to `.gitignore`
- Change `SECRET_KEY` before production
- In production, move user auth to Firebase Authentication
- Enable Firestore security rules for production

---

## 🛠️ Tech Stack

| Layer    | Technology              |
|----------|-------------------------|
| Frontend | HTML5, CSS3, JavaScript |
| Backend  | Python 3.11 + Flask 3   |
| Database | Firebase Firestore      |
| Charts   | Chart.js 4              |
| QR Codes | qrcode + Pillow         |
| Icons    | Font Awesome 6          |
| Fonts    | Syne + DM Sans          |
