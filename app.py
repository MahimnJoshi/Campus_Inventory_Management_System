from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from functools import wraps
import os
import json
from datetime import datetime
import qrcode
import io
import base64
from pymongo import MongoClient

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'campus-inventory-secret-2024')

# ─── MongoDB Initialization ──────────────────────────────────────────────────
# Reads MONGO_URI from your .env file. Defaults to local database if empty.
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/')
try:
    # 2-second timeout setup to prevent the server from hanging if URI is wrong
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
    client.server_info()  # Forces a connection verification check
    db = client['campus_inventory']
    MONGO_AVAILABLE = True
    print("Successfully connected to MongoDB!")
except Exception as e:
    print(f"MongoDB not configured or unreachable: {e}")
    MONGO_AVAILABLE = False
    db = None

# ─── Demo Users ───────────────────────────────────────────────────────────────
DEMO_USERS = {
    'admin@campus.edu': {'password': 'admin123', 'role': 'admin', 'name': 'Admin User'},
    'staff@campus.edu': {'password': 'staff123', 'role': 'staff', 'name': 'Staff Member'},
}

# ─── In-memory fallback store ─────────────────────────────────────────────────
DEMO_ITEMS = [
    {'id': 'ITEM001', 'name': 'Dell Laptop', 'category': 'Electronics', 'quantity': 15,
     'department': 'Computer Science', 'status': 'Available', 'threshold': 5,
     'created_at': '2024-01-10', 'updated_at': '2024-01-10'},
    {'id': 'ITEM002', 'name': 'Projector', 'category': 'Electronics', 'quantity': 3,
     'department': 'Physics', 'status': 'In Use', 'threshold': 2,
     'created_at': '2024-01-11', 'updated_at': '2024-01-11'},
    {'id': 'ITEM003', 'name': 'Lab Chair', 'category': 'Furniture', 'quantity': 50,
     'department': 'Chemistry', 'status': 'Available', 'threshold': 10,
     'created_at': '2024-01-12', 'updated_at': '2024-01-12'},
    {'id': 'ITEM004', 'name': 'Microscope', 'category': 'Lab Equipment', 'quantity': 2,
     'department': 'Biology', 'status': 'Damaged', 'threshold': 3,
     'created_at': '2024-01-13', 'updated_at': '2024-01-13'},
    {'id': 'ITEM005', 'name': 'Whiteboard', 'category': 'Furniture', 'quantity': 8,
     'department': 'Mathematics', 'status': 'Available', 'threshold': 2,
     'created_at': '2024-01-14', 'updated_at': '2024-01-14'},
    {'id': 'ITEM006', 'name': 'HP Printer', 'category': 'Electronics', 'quantity': 4,
     'department': 'Administration', 'status': 'Available', 'threshold': 2,
     'created_at': '2024-01-15', 'updated_at': '2024-01-15'},
]
DEMO_LOGS = []

# ─── Auth Helpers ─────────────────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        if session['user'].get('role') != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated

# ─── DB Helpers (Refactored for MongoDB) ──────────────────────────────────────
def get_items():
    if MONGO_AVAILABLE:
        docs = db.inventory.find()
        # Maps MongoDB's native '_id' key safely back to 'id' for layout templates
        return [{'id': d['_id'], **{k: v for k, v in d.items() if k != '_id'}} for d in docs]
    return DEMO_ITEMS.copy()

def get_item(item_id):
    if MONGO_AVAILABLE:
        doc = db.inventory.find_one({'_id': item_id})
        return {'id': doc['_id'], **{k: v for k, v in doc.items() if k != '_id'}} if doc else None
    return next((i for i in DEMO_ITEMS if i['id'] == item_id), None)

def save_item(item_id, data):
    if MONGO_AVAILABLE:
        # upsert=True handles both adding new entries and updating modifications seamlessly
        db.inventory.update_one({'_id': item_id}, {'$set': data}, upsert=True)
    else:
        existing = next((i for i in DEMO_ITEMS if i['id'] == item_id), None)
        if existing:
            existing.update(data)
        else:
            DEMO_ITEMS.append({'id': item_id, **data})

def delete_item_db(item_id):
    if MONGO_AVAILABLE:
        db.inventory.delete_one({'_id': item_id})
    else:
        global DEMO_ITEMS
        DEMO_ITEMS = [i for i in DEMO_ITEMS if i['id'] != item_id]

def log_action(action, item_id, item_name, user):
    entry = {
        'action': action,
        'item_id': item_id,
        'item_name': item_name,
        'user': user,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    if MONGO_AVAILABLE:
        db.activity_logs.insert_one(entry)
    else:
        DEMO_LOGS.insert(0, entry)
        if len(DEMO_LOGS) > 100:
            DEMO_LOGS.pop()

def get_logs():
    if MONGO_AVAILABLE:
        # Sorts by timestamp matching standard descending order (-1) limit up to 50
        docs = db.activity_logs.find().sort('timestamp', -1).limit(50)
        return [{k: v for k, v in d.items() if k != '_id'} for d in docs]
    return DEMO_LOGS[:50]

# ─── Routes ───────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        user = DEMO_USERS.get(email)
        if user and user['password'] == password:
            session['user'] = {'email': email, 'role': user['role'], 'name': user['name']}
            return jsonify({'success': True, 'role': user['role'], 'name': user['name']})
        return jsonify({'success': False, 'error': 'Invalid credentials'}), 401
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', user=session['user'])

@app.route('/inventory')
@login_required
def inventory():
    return render_template('inventory.html', user=session['user'])

@app.route('/reports')
@login_required
def reports():
    return render_template('reports.html', user=session['user'])

@app.route('/logs')
@login_required
def logs():
    return render_template('logs.html', user=session['user'])

# ─── API Endpoints ────────────────────────────────────────────────────────────
@app.route('/api/items', methods=['GET'])
@login_required
def api_get_items():
    items = get_items()
    search = request.args.get('search', '').lower()
    dept = request.args.get('department', '')
    status = request.args.get('status', '')
    category = request.args.get('category', '')

    if search:
        items = [i for i in items if search in i['name'].lower() or search in i['category'].lower()]
    if dept:
        items = [i for i in items if i.get('department') == dept]
    if status:
        items = [i for i in items if i.get('status') == status]
    if category:
        items = [i for i in items if i.get('category') == category]

    return jsonify(items)

@app.route('/api/items', methods=['POST'])
@login_required
def api_add_item():
    data = request.get_json()
    item_id = data.get('id', '').strip()
    if not item_id:
        return jsonify({'error': 'Item ID is required'}), 400

    existing = get_item(item_id)
    if existing:
        return jsonify({'error': 'Item ID already exists'}), 409

    now = datetime.now().strftime('%Y-%m-%d')
    item = {
        'name': data['name'],
        'category': data['category'],
        'quantity': int(data['quantity']),
        'department': data['department'],
        'status': data['status'],
        'threshold': int(data.get('threshold', 5)),
        'created_at': now,
        'updated_at': now,
    }
    save_item(item_id, item)
    log_action('ADD', item_id, data['name'], session['user']['email'])
    return jsonify({'success': True, 'id': item_id})

@app.route('/api/items/<item_id>', methods=['GET'])
@login_required
def api_get_item(item_id):
    item = get_item(item_id)
    if not item:
        return jsonify({'error': 'Not found'}), 404
    return jsonify(item)

@app.route('/api/items/<item_id>', methods=['PUT'])
@login_required
def api_update_item(item_id):
    data = request.get_json()
    existing = get_item(item_id)
    if not existing:
        return jsonify({'error': 'Not found'}), 404

    role = session['user']['role']
    if role == 'staff':
        allowed = ['quantity', 'status']
        update = {k: v for k, v in data.items() if k in allowed}
    else:
        update = data

    update['updated_at'] = datetime.now().strftime('%Y-%m-%d')
    if 'quantity' in update:
        update['quantity'] = int(update['quantity'])
    if 'threshold' in update:
        update['threshold'] = int(update['threshold'])

    existing.update(update)
    save_item(item_id, {k: v for k, v in existing.items() if k != 'id'})
    log_action('UPDATE', item_id, existing['name'], session['user']['email'])
    return jsonify({'success': True})

@app.route('/api/items/<item_id>', methods=['DELETE'])
@admin_required
def api_delete_item(item_id):
    item = get_item(item_id)
    if not item:
        return jsonify({'error': 'Not found'}), 404
    name = item['name']
    delete_item_db(item_id)
    log_action('DELETE', item_id, name, session['user']['email'])
    return jsonify({'success': True})

@app.route('/api/stats', methods=['GET'])
@login_required
def api_stats():
    items = get_items()
    total = len(items)
    total_qty = sum(i.get('quantity', 0) for i in items)

    categories = {}
    for i in items:
        cat = i.get('category', 'Other')
        categories[cat] = categories.get(cat, 0) + 1

    status_counts = {'Available': 0, 'In Use': 0, 'Damaged': 0}
    for i in items:
        s = i.get('status', 'Available')
        status_counts[s] = status_counts.get(s, 0) + 1

    departments = {}
    for i in items:
        dept = i.get('department', 'Other')
        departments[dept] = departments.get(dept, 0) + i.get('quantity', 0)

    low_stock = [i for i in items if i.get('quantity', 0) <= i.get('threshold', 5)]

    return jsonify({
        'total_items': total,
        'total_quantity': total_qty,
        'categories': categories,
        'status_counts': status_counts,
        'departments': departments,
        'low_stock': low_stock,
        'low_stock_count': len(low_stock),
    })

@app.route('/api/qr/<item_id>', methods=['GET'])
@login_required
def api_qr(item_id):
    item = get_item(item_id)
    if not item:
        return jsonify({'error': 'Not found'}), 404

    qr_data = json.dumps({'id': item_id, 'name': item['name'], 'department': item.get('department')})
    qr = qrcode.QRCode(version=1, box_size=8, border=2)
    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill_color='#0f172a', back_color='white')
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    b64 = base64.b64encode(buf.getvalue()).decode()
    return jsonify({'qr': f'data:image/png;base64,{b64}', 'item': item})

@app.route('/api/logs', methods=['GET'])
@login_required
def api_logs():
    return jsonify(get_logs())

@app.route('/api/session', methods=['GET'])
def api_session():
    if 'user' in session:
        return jsonify({'logged_in': True, 'user': session['user']})
    return jsonify({'logged_in': False})

if __name__ == '__main__':
    # ─── Automated MongoDB Atlas Migration Hook ───
    if MONGO_AVAILABLE:
        # Check if the inventory collection is completely fresh and empty
        if db.inventory.count_documents({}) == 0:
            print("🚀 Cloud database is empty! Performing structural asset seed migration to Atlas...")
            migration_batch = []
            for item in DEMO_ITEMS:
                doc = {
                    '_id': item['id'],  # Assigns string item IDs cleanly as primary key indexes
                    'name': item['name'],
                    'category': item['category'],
                    'quantity': item['quantity'],
                    'department': item['department'],
                    'status': item['status'],
                    'threshold': item['threshold'],
                    'created_at': item['created_at'],
                    'updated_at': item['updated_at']
                }
                migration_batch.append(doc)
            
            # Fire bulk operation down the cluster connection pipeline
            db.inventory.insert_many(migration_batch)
            print("✅ Migration process successful! Default documents are now live in your Atlas Cluster.")
        else:
            print("📁 Existing cloud datasets located inside inventory namespace. Skipping migration.")

    # Boot the application instance on localhost port 5000
    app.run(debug=True, port=5000)