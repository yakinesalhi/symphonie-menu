import sqlite3
import os
import qrcode
import io
from functools import wraps
from flask import Flask, request, jsonify, render_template_string, send_file, Response

app = Flask(__name__)

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "symphonie_pro.db")

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    try:
        conn = get_db()
        conn.execute('CREATE TABLE IF NOT EXISTS categories (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL)')
        conn.execute('CREATE TABLE IF NOT EXISTS menu_items (id INTEGER PRIMARY KEY AUTOINCREMENT, category_id INTEGER, name TEXT NOT NULL, price REAL DEFAULT 0, available INTEGER DEFAULT 1)')
        
        if conn.execute("SELECT COUNT(*) FROM categories").fetchone()[0] == 0:
            cats = [
                "Les plats gastro volailles", "Viande Rouge", "Entre Chaude", 
                "Les plats traditionnels", "Nos Brochettes", "Pasta", 
                "Fast food", "Nos poissons", "Boissons fraiches", 
                "Boissons Chaudes", "Dessert"
            ]
            for c in cats:
                conn.execute("INSERT INTO categories (name) VALUES (?)", (c,))
            
            items_data = [
                (1, 'Escalope de poulet grillé'), (1, 'Escalope à la crème'), (1, 'Escalope panée'), (1, 'Escalope malinaise'), 
                (1, 'Escalope à bormjaina'), (1, 'Kabab de volai'), (1, 'Cordent bleu'), (1, 'Cuisse mariné'), (1, 'Cuisse pané'),
                (2, 'Entrecôte du boeuf grillé'), (2, 'Entrecôte normande'), (2, 'Entrecôte chassure'), (2, 'Entrecôte bour de laisse'), 
                (2, 'Entrecôte sauce motard'), (2, 'Mix grillade'), (2, 'Filet sauce barbecue'), (2, 'Filet'),
                (3, 'Crème de volai'), (3, 'Soupe de poisson'), (3, 'Soupe de légumes'), (3, 'Chorba frik'), (3, 'Herira'), 
                (3, 'Bastila'), (3, 'Bourak viande'), (3, 'Bourak poulet'), (3, 'Brik annabi viande'), (3, 'Brik annabi Poulet'), 
                (3, 'Bourek crevette'), (3, 'Omlette au choix'), (3, 'Omlette royale'), (3, 'Gratin poulet'), (3, 'Gratin viande'), 
                (3, 'Gratin crevette'), (3, 'Gratin mixte'), (3, 'Gratin fruit de mer'),
                (4, "Chakhchoukha m'sila"), (4, 'Chakhchoukha bisekra'), (4, 'Chakhchoukha constantine (Trida)'), (4, 'Rechta'), 
                (4, 'Zeviti'), (4, 'Couscous'), (4, 'Chtitha lsen'), (4, 'Chtitha Viande'), (4, 'Chtitha Moukh'), (4, 'Douwara'), 
                (4, 'Tadjin zitoune'), (4, 'Jelbana'), (4, 'Mtouwem'), (4, 'Kebab'), (4, 'Aaja'), (4, 'Les abats'), 
                (4, 'Poulet mfouwer'), (4, 'Viande mfouwer'), (4, 'Bouzelouf'), (4, 'Mechoui (poids)'), (4, 'Cuisse roté'),
                (5, 'Steak hachée'), (5, 'Tranche de foi'), (5, 'Brochette de foi dinde royal'), (5, 'Brochette merguez'), 
                (5, 'Brochette de viande royal'), (5, 'Brochette de foie de veau'), (5, 'Brochette melfouf'), (5, 'Brochette kabab'), 
                (5, 'Entrecôte de boeuf'), (5, "Cote d'agneau"), (5, 'Melange foie + dinde + viande'),
                (6, 'Spaghetti bolognaise'), (6, 'Spaghetti napolitain'), (6, 'Spaghetti fruits de mer'), (6, 'Spaghetti quatre fromages'), 
                (6, 'Tagliatelle poulet champignons'), (6, 'Tagliatelle quatre fromages'), (6, 'Tagliatelle saumon'), 
                (6, 'Tagliatelle camembert'), (6, 'Les linguine aux crevette'),
                (7, 'Tacos poulet'), (7, 'Tacos viande'), (7, 'Tacos crispy'), (7, 'Tacos Mixte'), (7, 'Burger poulet'), 
                (7, 'Burger viande'), (7, 'Burger mixte'), (7, 'Burger crispy'), (7, 'Menu enfant au choix'),
                (8, 'Dorade'), (8, 'Saumon'), (8, 'Calamar'), (8, 'Loup de mer'), (8, 'Sipia en sauce'), (8, 'Espadon'), 
                (8, 'Crevette grillé'), (8, 'Crevette en sauce'), (8, 'Sardine'), (8, 'Rouget'), (8, 'Pageot'), (8, 'Marbre'), 
                (8, 'Brouché'), (8, 'Pagre'), (8, 'Mix poisson'),
                (9, 'Eau GM'), (9, 'Eau PM'), (9, 'Coca 1L'), (9, 'Hamoud 1L'), (9, 'Hamoud Canette'), (9, 'Coca cola canette'), 
                (9, 'Eau non gazeuse'), (9, "Jus d'orange nature"), (9, 'Jus de citrone nature'), (9, 'Mujito'), (9, 'Jus cocktail'), 
                (9, 'Jus Symphonie'), (9, 'Milkshake'), (9, 'Café glacé'), (9, 'Jus de banane'), (9, 'Jus de fraise'),
                (10, 'Café nesspresso'), (10, 'Thé maison Timimoun'), (10, 'Thé lipton au choix'), (10, 'Tisane maison au choix'),
                (11, 'Crépe simple'), (11, 'Crépe au fruit'), (11, 'Crépe surprise'), (11, 'Crépe banane'), (11, 'Crépe maison'), 
                (11, 'Gaufre simple'), (11, 'Gaufre au fruit'), (11, 'Gaufre surprise'), (11, 'Gaufre banane'), (11, 'Fondant chocolat'), 
                (11, 'Mousse chocolat'), (11, 'Crème broulée'), (11, 'Crème caramel'), (11, 'Crème tiramisu'), (11, 'Salade de fruits'), 
                (11, 'Assiette de fruits')
            ]
            
            for cat_id, name in items_data:
                conn.execute("INSERT INTO menu_items (category_id, name, price) VALUES (?, ?, 0)", (cat_id, name))
            
            conn.commit()
        conn.close()
    except Exception as e:
        print(f"Erreur DB init: {e}")

init_db()

# --- SÉCURITÉ ---
def check_auth(username, password):
    return username == 'admin' and password == 'symphonie2026'

def authenticate():
    return Response(
        'Accès refusé. Authentification requise.', 401,
        {'WWW-Authenticate': 'Basic realm="Espace Gerant Symphonie"'}
    )

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

# --- ROUTES API ---
@app.route('/api/menu')
def get_menu():
    try:
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
    except Exception as e:
        return jsonify([])

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

# --- VUES PAGES ET QR CODE ---
HTML_CLIENT = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>خيمة السيمفونية - Menu Numérique</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background-color: #121212; color: #e0e0e0; font-family: 'Segoe UI', sans-serif; padding-bottom: 30px;}
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
        <div id="menuContainer"><div class="text-center text-warning mt-5">Chargement du menu...</div></div>
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
                document.getElementById('menuContainer').innerHTML = '<div class="text-center text-danger mt-5">Erreur de chargement.</div>';
            }
        }
        function renderNav() {
            const nav = document.getElementById('categoryNav');
            nav.innerHTML = `<button class="btn category-badge active" onclick="filterCat('all', this)">Tous</button>`;
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

HTML_ADMIN = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Espace Gérant - Symphonie</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        body { background: #f4f6f9; padding-bottom: 50px; font-family: 'Segoe UI', sans-serif; }
        .admin-header { background: #1a160d; color: #d4af37; padding: 20px; text-align: center; border-bottom: 3px solid #d4af37; margin-bottom: 25px; }
        .card { border: none; border-radius: 12px; box-shadow: 0 4px 8px rgba(0,0,0,0.05); margin-bottom: 20px; overflow: hidden; }
        .item-row { display: flex; justify-content: space-between; align-items: center; padding: 12px 15px; border-bottom: 1px solid #eee; background: white;}
        .item-name { font-weight: 600; color: #333; }
        .controls-group { display: flex; align-items: center; gap: 8px; }
    </style>
</head>
<body>
    <div class="admin-header d-flex justify-content-between align-items-center px-4">
        <div></div>
        <div>
            <h3 class="m-0"><i class="fas fa-cogs"></i> Tableau de Bord Gérant</h3>
        </div>
        <div>
            <a href="/admin/download-qrcode" class="btn btn-warning fw-bold"><i class="fas fa-qrcode"></i> Télécharger le QR Code</a>
        </div>
    </div>
    <div class="container">
        <div class="row mb-4">
            <div class="col-md-6 mb-3">
                <div class="card h-100"><div class="card-body">
                    <h6 class="text-primary fw-bold"><i class="fas fa-folder-plus"></i> Nouvelle Catégorie</h6>
                    <div class="d-flex gap-2 mt-3">
                        <input type="text" id="newCatName" class="form-control" placeholder="Nom de la catégorie">
                        <button class="btn btn-primary px-4" onclick="addCategory()">Ajouter</button>
                    </div>
                </div></div>
            </div>
            <div class="col-md-6 mb-3">
                <div class="card h-100"><div class="card-body">
                    <h6 class="text-success fw-bold"><i class="fas fa-plus-circle"></i> Nouveau Plat</h6>
                    <div class="d-flex gap-2 flex-wrap mt-3">
                        <select id="newItemCat" class="form-select w-100"></select>
                        <input type="text" id="newItemName" class="form-control" placeholder="Nom du plat" style="flex: 2;">
                        <input type="number" id="newItemPrice" class="form-control" placeholder="Prix" style="flex: 1;">
                        <button class="btn btn-success" onclick="addItem()">Ajouter</button>
                    </div>
                </div></div>
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
                let html = `<div class="card"><div class="bg-dark text-white p-3 d-flex justify-content-between align-items-center">
                    <h5 class="m-0 text-warning">${cat.category}</h5>
                    <button class="btn btn-sm btn-outline-danger" onclick="deleteCategory(${cat.id})"><i class="fas fa-trash"></i></button>
                </div>`;
                if(cat.items.length === 0) {
                    html += `<div class="p-3 text-center text-muted">Aucun plat.</div>`;
                } else {
                    cat.items.forEach(item => {
                        html += `<div class="item-row">
                            <div class="item-name">${item.name}</div>
                            <div class="controls-group">
                                <input type="number" class="form-control form-control-sm text-center" style="width: 80px;" value="${item.price}" onchange="updatePrice(${item.id}, this.value)">
                                <button class="btn btn-sm ${item.available ? 'btn-success' : 'btn-secondary'}" onclick="toggle(${item.id})" style="width: 90px;">
                                    ${item.available ? 'Stock' : 'Rupture'}
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
            await fetch('/api/categories', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({name})});
            document.getElementById('newCatName').value = '';
            loadData();
        }
        async function deleteCategory(id) {
            if(confirm("Supprimer cette catégorie et ses plats ?")) {
                await fetch(`/api/categories/${id}`, {method: 'DELETE'});
                loadData();
            }
        }
        async function addItem() {
            const category_id = document.getElementById('newItemCat').value;
            const name = document.getElementById('newItemName').value;
            const price = document.getElementById('newItemPrice').value;
            if(!category_id || !name) return alert("Remplissez le nom et la catégorie.");
            await fetch('/api/items', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({category_id, name, price: parseFloat(price||0)})});
            document.getElementById('newItemName').value = '';
            document.getElementById('newItemPrice').value = '';
            loadData();
        }
        async function deleteItem(id) {
            if(confirm("Supprimer ce plat ?")) {
                await fetch(`/api/items/${id}`, {method: 'DELETE'});
                loadData();
            }
        }
        async function toggle(id) {
            await fetch(`/api/toggle/${id}`, {method: 'POST'});
            loadData();
        }
        async function updatePrice(id, price) {
            await fetch(`/api/update-price/${id}`, {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({price: parseFloat(price)})});
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
@requires_auth
def admin_page():
    return render_template_string(HTML_ADMIN)

@app.route('/admin/download-qrcode')
@requires_auth
def download_qrcode():
    base_url = request.host_url.rstrip('/')
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(base_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return send_file(buffer, mimetype='image/png', as_attachment=True, download_name='qrcode_symphonie.png')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)