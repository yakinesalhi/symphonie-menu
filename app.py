import sqlite3
import os
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# Base de données
DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "symphonie_pro.db")

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    try:
        conn = get_db()
        conn.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS menu_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER,
                name TEXT NOT NULL,
                price REAL DEFAULT 0,
                available INTEGER DEFAULT 1,
                FOREIGN KEY (category_id) REFERENCES categories (id)
            )
        ''')
        
        # Remplissage automatique si la base est vide
        if conn.execute("SELECT COUNT(*) FROM categories").fetchone()[0] == 0:
            cats = ["Les plats gastro volailles", "Viande Rouge", "Entrée Chaude", "Boissons fraîches", "Dessert"]
            for c in cats:
                conn.execute("INSERT INTO categories (name) VALUES (?)", (c,))
            
            # Quelques plats par défaut
            items_data = [
                (1, 'Escalope de poulet grillé', 800), (1, 'Cordon bleu', 1000),
                (2, 'Entrecôte du boeuf grillé', 1500), (3, 'Chorba frik', 400),
                (4, 'Coca cola canette', 150), (4, 'Jus d\'orange naturel', 300),
                (5, 'Fondant chocolat', 450)
            ]
            for cat_id, name, price in items_data:
                conn.execute("INSERT INTO menu_items (category_id, name, price) VALUES (?, ?, ?)", (cat_id, name, price))
            conn.commit()
        conn.close()
    except Exception as e:
        print(f"Erreur DB: {e}")

init_db()

# ================= API ENDPOINTS =================

@app.route('/api/menu')
def get_menu():
    init_db() # <-- LE CORRECTIF EST ICI (Auto-réparation systématique)
    conn = get_db()
    cats = conn.execute("SELECT * FROM categories ORDER BY id").fetchall()
    result = []
    for cat in cats:
        items = conn.execute("SELECT * FROM menu_items WHERE category_id = ?", (cat['id'],)).fetchall()
        result.append({
            'id': cat['id'],
            'category': cat['name'],
            'items': [dict(i) for i in items]
        })
    conn.close()
    return jsonify(result)

@app.route('/api/categories', methods=['POST'])
def add_category():
    name = request.json.get('name')
    conn = get_db()
    try:
        conn.execute("INSERT INTO categories (name) VALUES (?)", (name,))
        conn.commit()
    except:
        pass
    conn.close()
    return jsonify({'success': True})

@app.route('/api/categories/<int:id>', methods=['DELETE'])
def delete_category(id):
    conn = get_db()
    conn.execute("DELETE FROM menu_items WHERE category_id = ?", (id,))
    conn.execute("DELETE FROM categories WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/items', methods=['POST'])
def add_item():
    data = request.json
    conn = get_db()
    conn.execute("INSERT INTO menu_items (category_id, name, price) VALUES (?, ?, ?)", 
                 (data['category_id'], data['name'], data['price']))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/items/<int:id>', methods=['DELETE'])
def delete_item(id):
    conn = get_db()
    conn.execute("DELETE FROM menu_items WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/toggle/<int:id>', methods=['POST'])
def toggle_item(id):
    conn = get_db()
    conn.execute("UPDATE menu_items SET available = CASE WHEN available = 1 THEN 0 ELSE 1 END WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/update-price/<int:id>', methods=['POST'])
def update_price(id):
    price = request.json.get('price', 0)
    conn = get_db()
    conn.execute("UPDATE menu_items SET price = ? WHERE id = ?", (price, id))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


# ================= FRONTEND CLIENT (MENU SOMBRE) =================
HTML_CLIENT = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>خيمة السيمفونية - Menu Numérique</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background-color: #121212; color: #e0e0e0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; padding-bottom: 30px;}
        .hero { text-align: center; padding: 30px 15px; background: linear-gradient(180deg, #1f1a0e 0%, #121212 100%); border-bottom: 1px solid #332a15; }
        .brand-title { color: #d4af37; font-size: 2.2rem; font-weight: bold; margin-bottom: 0; }
        .brand-subtitle { color: #f3e5ab; font-size: 1.2rem; font-style: italic; }
        .category-badge { background-color: #242424; color: #d4af37; border: 1px solid #d4af37; margin: 4px; border-radius: 20px; font-size: 0.9rem; white-space: nowrap;}
        .category-badge.active { background-color: #d4af37; color: #121212; font-weight: bold; }
        .menu-card { background-color: #1a1a1a; border: 1px solid #2a2a2a; border-radius: 10px; margin-bottom: 12px; padding: 15px; display: flex; justify-content: space-between; align-items: center; }
        .item-name { font-size: 1.1rem; color: #ffffff; font-weight: 500; }
        .item-price { font-size: 1.1rem; color: #d4af37; font-weight: bold; }
        .out-of-stock { opacity: 0.5; text-decoration: line-through; }
        .badge-rupture { background-color: #dc3545; color: white; font-size: 0.75rem; padding: 3px 8px; border-radius: 4px; }
        .search-box { background-color: #1a1a1a; border: 1px solid #333; color: white; border-radius: 25px; padding: 10px 20px; }
        .search-box:focus { background-color: #222; color: white; border-color: #d4af37; box-shadow: none; }
        ::-webkit-scrollbar { height: 6px; }
        ::-webkit-scrollbar-thumb { background: #d4af37; border-radius: 10px; }
    </style>
</head>
<body>
    <div class="hero">
        <h1 class="brand-title">خيمة السيمفونية</h1>
        <div class="brand-subtitle">Symphonie Restaurant</div>
    </div>
    <div class="container py-3">
        <input type="text" id="searchInput" class="form-control search-box mb-3" placeholder="🔍 Rechercher un plat, boisson...">
        <div id="categoryNav" class="d-flex overflow-auto pb-2 mb-3"></div>
        <div id="menuContainer">
            <div class="text-center text-warning mt-5">Chargement du menu en cours...</div>
        </div>
    </div>

    <script>
        let fullMenu = [];
        async function loadMenu() {
            try {
                const res = await fetch('/api/menu');
                fullMenu = await res.json();
                renderNav();
                renderMenu(fullMenu);
            } catch (e) {
                document.getElementById('menuContainer').innerHTML = '<div class="text-center text-danger mt-5">Erreur de connexion. Veuillez rafraîchir la page.</div>';
            }
        }
        function renderNav() {
            const nav = document.getElementById('categoryNav');
            nav.innerHTML = '<button class="btn category-badge active" onclick="filterCat(\'all\', this)">Tous</button>';
            fullMenu.forEach(c => {
                nav.innerHTML += `<button class="btn category-badge" onclick="filterCat(${c.id}, this)">${c.category}</button>`;
            });
        }
        function filterCat(id, btn) {
            document.querySelectorAll('.category-badge').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            renderMenu(id === 'all' ? fullMenu : fullMenu.filter(c => c.id === id));
        }
        function renderMenu(data) {
            const container = document.getElementById('menuContainer');
            container.innerHTML = '';
            data.forEach(cat => {
                if(cat.items.length === 0) return;
                let html = `<h4 class="text-warning mt-4 mb-3 border-bottom border-secondary pb-1">${cat.category}</h4>`;
                cat.items.forEach(item => {
                    html += `
                        <div class="menu-card ${!item.available ? 'out-of-stock' : ''}">
                            <div>
                                <span class="item-name">${item.name}</span>
                                ${!item.available ? '<br><span class="badge-rupture">Non disponible</span>' : ''}
                            </div>
                            <div class="item-price">${item.price > 0 ? item.price + ' DA' : '—'}</div>
                        </div>`;
                });
                container.innerHTML += html;
            });
        }
        document.getElementById('searchInput').addEventListener('input', (e) => {
            const term = e.target.value.toLowerCase();
            const filtered = fullMenu.map(cat => ({
                ...cat, items: cat.items.filter(i => i.name.toLowerCase().includes(term))
            })).filter(cat => cat.items.length > 0);
            renderMenu(filtered);
        });
        loadMenu();
    </script>
</body>
</html>
"""

# ================= FRONTEND ADMIN GÉRANT =================
HTML_ADMIN = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Espace Gérant - Symphonie</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        body { background: #f4f6f9; padding-bottom: 50px; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        .admin-header { background: #1a160d; color: #d4af37; padding: 20px; text-align: center; border-bottom: 3px solid #d4af37; margin-bottom: 25px; }
        .card { border: none; border-radius: 12px; box-shadow: 0 4px 8px rgba(0,0,0,0.05); margin-bottom: 20px; overflow: hidden; }
        .item-row { display: flex; justify-content: space-between; align-items: center; padding: 12px 15px; border-bottom: 1px solid #eee; background: white;}
        .item-row:last-child { border-bottom: none; }
        .item-name { font-weight: 600; color: #333; }
        .btn-gold { background-color: #d4af37; color: #000; font-weight: bold; }
        .controls-group { display: flex; align-items: center; gap: 8px; }
    </style>
</head>
<body>
    <div class="admin-header">
        <h3 class="m-0"><i class="fas fa-cogs"></i> Tableau de Bord Gérant</h3>
        <small class="text-light opacity-75">Gérez vos catégories, plats et prix en temps réel</small>
    </div>

    <div class="container">
        <div class="row mb-4">
            <div class="col-md-6 mb-3">
                <div class="card h-100">
                    <div class="card-body">
                        <h6 class="text-primary fw-bold"><i class="fas fa-folder-plus"></i> Nouvelle Catégorie</h6>
                        <div class="d-flex gap-2 mt-3">
                            <input type="text" id="newCatName" class="form-control" placeholder="Ex: Pizzas, Salades...">
                            <button class="btn btn-primary px-4" onclick="addCategory()">Ajouter</button>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-6 mb-3">
                <div class="card h-100">
                    <div class="card-body">
                        <h6 class="text-success fw-bold"><i class="fas fa-plus-circle"></i> Nouveau Plat</h6>
                        <div class="d-flex gap-2 flex-wrap mt-3">
                            <select id="newItemCat" class="form-select w-100"></select>
                            <input type="text" id="newItemName" class="form-control" placeholder="Nom du plat" style="flex: 2;">
                            <input type="number" id="newItemPrice" class="form-control" placeholder="Prix" style="flex: 1;">
                            <button class="btn btn-success" onclick="addItem()">Ajouter</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <h4 class="mb-3 text-secondary border-bottom pb-2">Menu Actuel</h4>
        <div id="adminMenu"></div>
    </div>

    <script>
        let fullMenu = [];

        async function loadData() {
            const res = await fetch('/api/menu');
            fullMenu = await res.json();
            
            const select = document.getElementById('newItemCat');
            select.innerHTML = '<option value="">Choisir la catégorie...</option>';
            fullMenu.forEach(c => select.innerHTML += `<option value="${c.id}">${c.category}</option>`);

            const container = document.getElementById('adminMenu');
            container.innerHTML = '';
            
            fullMenu.forEach(cat => {
                let html = `
                <div class="card">
                    <div class="bg-dark text-white p-3 d-flex justify-content-between align-items-center">
                        <h5 class="m-0 text-warning">${cat.category}</h5>
                        <button class="btn btn-sm btn-outline-danger" onclick="deleteCategory(${cat.id})" title="Supprimer la catégorie"><i class="fas fa-trash"></i></button>
                    </div>
                `;
                
                if(cat.items.length === 0) {
                    html += `<div class="p-3 text-center text-muted">Aucun plat dans cette catégorie.</div>`;
                } else {
                    cat.items.forEach(item => {
                        html += `
                        <div class="item-row">
                            <div class="item-name">${item.name}</div>
                            <div class="controls-group">
                                <input type="number" class="form-control form-control-sm text-center" style="width: 80px;" value="${item.price}" onchange="updatePrice(${item.id}, this.value)">
                                <button class="btn btn-sm ${item.available ? 'btn-success' : 'btn-secondary'}" onclick="toggle(${item.id})" style="width: 90px;">
                                    ${item.available ? '<i class="fas fa-check"></i> Stock' : '<i class="fas fa-times"></i> Rupture'}
                                </button>
                                <button class="btn btn-sm btn-danger" onclick="deleteItem(${item.id})"><i class="fas fa-trash"></i></button>
                            </div>
                        </div>`;
                    });
                }
                html += `</div>`;
                container.innerHTML += html;
            });
        }

        async function addCategory() {
            const name = document.getElementById('newCatName').value;
            if(!name) return;
            await fetch('/api/categories', {
                method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({name})
            });
            document.getElementById('newCatName').value = '';
            loadData();
        }

        async function deleteCategory(id) {
            if(confirm("Attention : Cela supprimera la catégorie ET tous les plats à l'intérieur. Confirmer ?")) {
                await fetch(`/api/categories/${id}`, {method: 'DELETE'});
                loadData();
            }
        }

        async function addItem() {
            const category_id = document.getElementById('newItemCat').value;
            const name = document.getElementById('newItemName').value;
            const price = document.getElementById('newItemPrice').value;
            if(!category_id || !name) return alert("Veuillez remplir la catégorie et le nom du plat.");
            
            await fetch('/api/items', {
                method: 'POST', headers: {'Content-Type': 'application/json'}, 
                body: JSON.stringify({category_id, name, price: parseFloat(price||0)})
            });
            document.getElementById('newItemName').value = '';
            document.getElementById('newItemPrice').value = '';
            loadData();
        }

        async function deleteItem(id) {
            if(confirm("Supprimer définitivement ce plat ?")) {
                await fetch(`/api/items/${id}`, {method: 'DELETE'});
                loadData();
            }
        }

        async function toggle(id) {
            await fetch(`/api/toggle/${id}`, {method: 'POST'});
            loadData();
        }

        async function updatePrice(id, price) {
            await fetch(`/api/update-price/${id}`, {
                method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({price: parseFloat(price)})
            });
        }

        loadData();
    </script>
</body>
</html>
"""

@app.route('/')
def client_page():
    return render_template_string(HTML_CLIENT)

@app.route('/admin')
def admin_page():
    return render_template_string(HTML_ADMIN)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)