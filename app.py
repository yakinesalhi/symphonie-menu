import sqlite3
import os
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# Base de données simple et robuste
DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "symphonie.db")

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS menu (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            name TEXT NOT NULL,
            price REAL DEFAULT 0,
            available INTEGER DEFAULT 1
        )
    ''')
    cursor.execute("SELECT COUNT(*) FROM menu")
    if cursor.fetchone()[0] == 0:
        data = [
            (" Les plats gastro volailles", "Escalope de poulet grillé", 800),
            (" Les plats gastro volailles", "Escalope à la crème", 900),
            (" Les plats gastro volailles", "Cordon bleu", 1000),
            (" Viande Rouge", "Entrecôte du boeuf grillé", 1500),
            (" Viande Rouge", "Mix grillade", 1800),
            (" Entrée Chaude", "Chorba frik", 400),
            (" Entrée Chaude", "Bourak viande", 150),
            (" Les plats traditionnels", "Chakhchoukha bisekra", 700),
            (" Les plats traditionnels", "Rechta", 700),
            (" Fast food", "Tacos poulet", 500),
            (" Boissons fraîches", "Coca cola canette", 150),
            (" Boissons fraîches", "Jus d'orange naturel", 300),
            (" Boissons Chaudes", "Café nespresso", 100),
            (" Dessert", "Fondant chocolat", 400)
        ]
        cursor.executemany("INSERT INTO menu (category, name, price) VALUES (?, ?, ?)", data)
        conn.commit()
    conn.close()

init_db()

# --- API ---
@app.route('/api/menu')
def api_menu():
    init_db()
    conn = get_db()
    items = conn.execute("SELECT * FROM menu ORDER BY category, id").fetchall()
    conn.close()
    
    categories = {}
    for item in items:
        cat = item['category']
        if cat not in categories:
            categories[cat] = []
        categories[cat].append({
            'id': item['id'],
            'name': item['name'],
            'price': item['price'],
            'available': bool(item['available'])
        })
    return jsonify([{'category': k, 'items': v} for k, v in categories.items()])

@app.route('/api/toggle/<int:item_id>', methods=['POST'])
def toggle_item(item_id):
    conn = get_db()
    conn.execute("UPDATE menu SET available = CASE WHEN available = 1 THEN 0 ELSE 1 END WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/update-price/<int:item_id>', methods=['POST'])
def update_price(item_id):
    price = request.json.get('price', 0)
    conn = get_db()
    conn.execute("UPDATE menu SET price = ? WHERE id = ?", (price, item_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

# --- PAGE CLIENT (Menu QR Code) ---
@app.route('/')
def client_page():
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>خيمة السيمفونية</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body { background: #121212; color: #fff; font-family: sans-serif; padding-bottom: 30px; }
            .header { text-align: center; padding: 25px 10px; background: #1a160d; border-bottom: 2px solid #d4af37; }
            .title { color: #d4af37; font-size: 2rem; font-weight: bold; margin: 0; }
            .card-item { background: #1e1e1e; border: 1px solid #333; border-radius: 10px; padding: 12px 15px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; }
            .out { opacity: 0.4; text-decoration: line-through; }
            .badge-off { background: #dc3545; color: white; font-size: 0.7rem; padding: 2px 6px; border-radius: 4px; }
            .price { color: #d4af37; font-weight: bold; font-size: 1.1rem; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1 class="title">خيمة السيمفونية</h1>
            <small class="text-warning">Symphonie Restaurant</small>
        </div>
        <div class="container mt-3" id="app">Chargement...</div>
        <script>
            async function load() {
                const res = await fetch('/api/menu');
                const data = await res.json();
                let html = '';
                data.forEach(cat => {
                    html += `<h4 class="text-warning mt-4 border-bottom border-secondary pb-1">${cat.category}</h4>`;
                    cat.items.forEach(item => {
                        html += `
                            <div class="card-item ${!item.available ? 'out' : ''}">
                                <div>
                                    <strong>${item.name}</strong>
                                    ${!item.available ? '<br><span class="badge-off">Rupture de stock</span>' : ''}
                                </div>
                                <div class="price">${item.price} DA</div>
                            </div>`;
                    });
                });
                document.getElementById('app').innerHTML = html;
            }
            load();
        </script>
    </body>
    </html>
    ''')

# --- PAGE ADMIN SIMPLIFIÉE POUR LE GÉRANT ---
@app.route('/admin')
def admin_page():
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Gestion Menu - Gérant</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body { background: #f8f9fa; font-family: sans-serif; padding-bottom: 50px; }
            .item-row { background: white; border-radius: 8px; padding: 12px; margin-bottom: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); display: flex; justify-content: space-between; align-items: center; }
        </style>
    </head>
    <body>
        <div class="bg-dark text-white p-3 text-center mb-3">
            <h3 class="m-0">📱 Espace Gérant</h3>
            <small>Modifier les prix et les disponibilités</small>
        </div>
        <div class="container" id="adminApp">Chargement...</div>

        <script>
            async function loadAdmin() {
                const res = await fetch('/api/menu');
                const data = await res.json();
                let html = '';
                data.forEach(cat => {
                    html += `<h5 class="text-primary mt-3">${cat.category}</h5>`;
                    cat.items.forEach(item => {
                        html += `
                            <div class="item-row">
                                <div>
                                    <strong>${item.name}</strong>
                                </div>
                                <div class="d-flex align-items-center gap-2">
                                    <input type="number" class="form-control form-control-sm" style="width: 80px;" value="${item.price}" onchange="changePrice(${item.id}, this.value)">
                                    <button class="btn btn-sm ${item.available ? 'btn-success' : 'btn-danger'}" onclick="toggle(${item.id})">
                                        ${item.available ? 'En stock' : 'Rupture'}
                                    </button>
                                </div>
                            </div>`;
                    });
                });
                document.getElementById('adminApp').innerHTML = html;
            }

            async function toggle(id) {
                await fetch('/api/toggle/' + id, {method: 'POST'});
                loadAdmin();
            }

            async function changePrice(id, newPrice) {
                await fetch('/api/update-price/' + id, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({price: parseFloat(newPrice)})
                });
            }

            loadAdmin();
        </script>
    </body>
    </html>
    ''')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)