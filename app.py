import sqlite3
import os
import functools
from flask import Flask, request, jsonify, render_template_string, session
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Chemin absolu garanti pour Render et Gunicorn
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "symphonie_menu.db")

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            display_order INTEGER
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS menu_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER,
            name TEXT NOT NULL,
            price REAL DEFAULT 0.0,
            available INTEGER DEFAULT 1,
            FOREIGN KEY (category_id) REFERENCES categories (id)
        )
    ''')
    
    cursor.execute("SELECT * FROM admin WHERE username = 'admin'")
    if not cursor.fetchone():
        hashed_pass = generate_password_hash("Symphonie2026!", method='pbkdf2:sha256')
        cursor.execute("INSERT INTO admin (username, password_hash) VALUES (?, ?)", ('admin', hashed_pass))

    cursor.execute("SELECT COUNT(*) FROM categories")
    count = cursor.fetchone()[0]
    
    if count == 0:
        menu_data = {
            "Les plats gastro volailles": ["Escalope de poulet grillé", "Escalope à la crème", "Escalope panée", "Escalope malinaise", "Escalope à bormjaina", "Kabab de volaille", "Cordon bleu", "Cuisse marinée", "Cuisse panée"],
            "Viande Rouge": ["Entrecôte du boeuf grillé", "Entrecôte normande", "Entrecôte chasseur", "Entrecôte beurre de maître d'hôtel", "Entrecôte sauce moutarde", "Mix grillade", "Filet sauce barbecue", "Filet"],
            "Entrée Chaude": ["Crème de volaille", "Soupe de poisson", "Soupe de légumes", "Chorba frik", "Herira", "Bastila", "Bourak viande", "Bourak poulet", "Brik annabi viande", "Brik annabi poulet", "Bourek crevette", "Omelette au choix", "Omelette royale", "Gratin poulet", "Gratin viande", "Gratin crevette", "Gratin mixte", "Gratin fruit de mer"],
            "Les plats traditionnels": ["Chakhchoukha m'sila", "Chakhchoukha bisekra", "Chakhchoukha constantine (Trida)", "Rechta", "Zeviti", "Couscous", "Chtitha Isen", "Chtitha Viande", "Chtitha Moukh", "Douwara", "Tadjin zitoune", "Jelbana", "Mtouwem", "Kebab", "Aaja", "Les abats", "Poulet mfouwer", "Viande mfouwer", "Bouzelouf", "Mechoui (au poids)", "Cuisse rotie"],
            "Nos Brochettes": ["Steak haché", "Tranche de foie", "Brochette de foie dinde royal", "Brochette merguez", "Brochette de viande royal", "Brochette de foie de veau", "Brochette melfouf", "Brochette kabab", "Entrecôte de boeuf", "Côte d'agneau", "Mélange foie + dinde + viande"],
            "Pasta": ["Spaghetti bolognaise", "Spaghetti napolitain", "Spaghetti fruits de mer", "Spaghetti quatre fromages", "Tagliatelle poulet champignons", "Tagliatelle quatre fromages", "Tagliatelle saumon", "Tagliatelle camembert", "Les linguine aux crevettes"],
            "Fast food": ["Tacos poulet", "Tacos viande", "Tacos crispy", "Tacos mixte", "Burger poulet", "Burger viande", "Burger mixte", "Burger crispy", "Menu enfant au choix"],
            "Nos poissons": ["Dorade", "Saumon", "Calamar", "Loup de mer", "Sepia en sauce", "Espadon", "Crevette grillée", "Crevette en sauce", "Sardine", "Rouget", "Pageot", "Marbre", "Brouché", "Pagre", "Mix poisson"],
            "Boissons fraîches": ["Eau GM", "Eau PM", "Coca 1L", "Hamoud 1L", "Hamoud Canette", "Coca cola canette", "Eau non gazeuse", "Jus d'orange naturel", "Jus de citron naturel", "Mojito", "Jus cocktail", "Jus Symphonie", "Milkshake", "Café glacé", "Jus de banane", "Jus de fraise"],
            "Boissons Chaudes": ["Café nespresso", "Thé maison Timimoun", "Thé lipton au choix", "Tisane maison au choix"],
            "Dessert": ["Crêpe simple", "Crêpe au fruit", "Crêpe surprise", "Crêpe banane", "Crêpe maison", "Gaufre simple", "Gaufre au fruit", "Gaufre surprise", "Gaufre banane", "Fondant chocolat", "Mousse chocolat", "Crème brûlée", "Crème caramel", "Crème tiramisu", "Salade de fruits", "Assiette de fruits"]
        }
        
        order = 1
        for cat_name, items in menu_data.items():
            cursor.execute("INSERT INTO categories (name, display_order) VALUES (?, ?)", (cat_name, order))
            cat_id = cursor.lastrowid
            order += 1
            for item in items:
                cursor.execute("INSERT INTO menu_items (category_id, name, price, available) VALUES (?, ?, ?, 1)", (cat_id, item, 0.0))

    conn.commit()
    conn.close()

def login_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return jsonify({'error': 'Non autorisé'}), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route('/api/menu', methods=['GET'])
def get_menu():
    init_db()  # Auto-initialisation systématique
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM categories ORDER BY display_order")
    categories = cursor.fetchall()
    
    result = []
    for cat_id, cat_name in categories:
        cursor.execute("SELECT id, name, price, available FROM menu_items WHERE category_id = ?", (cat_id,))
        items = [{'id': r[0], 'name': r[1], 'price': r[2], 'available': bool(r[3])} for r in cursor.fetchall()]
        result.append({
            'id': cat_id,
            'category': cat_name,
            'items': items
        })
    conn.close()
    return jsonify(result)

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json or {}
    username = data.get('username')
    password = data.get('password')
    
    init_db()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT password_hash FROM admin WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()
    
    if row and check_password_hash(row[0], password):
        session['admin_logged_in'] = True
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': 'Identifiants incorrects'}), 401

@app.route('/api/admin/update-item', methods=['POST'])
@login_required
def update_item():
    data = request.json or {}
    item_id = data.get('id')
    price = data.get('price')
    available = 1 if data.get('available') else 0
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE menu_items SET price = ?, available = ? WHERE id = ?", (price, available, item_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

HTML_CLIENT = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>خيمة السيمفونية - Menu Numérique</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background-color: #121212; color: #e0e0e0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        .hero { text-align: center; padding: 30px 15px; background: linear-gradient(180deg, #1f1a0e 0%, #121212 100%); border-bottom: 1px solid #332a15; }
        .brand-title { color: #d4af37; font-size: 2.2rem; font-weight: bold; margin-bottom: 0; }
        .brand-subtitle { color: #f3e5ab; font-size: 1.2rem; font-style: italic; }
        .category-badge { background-color: #242424; color: #d4af37; border: 1px solid #d4af37; margin: 4px; border-radius: 20px; font-size: 0.9rem; }
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
        <p class="text-muted small mt-1">Menu Digital Officiel</p>
    </div>

    <div class="container py-3">
        <input type="text" id="searchInput" class="form-control search-box mb-3" placeholder="🔍 Rechercher un plat, boisson...">
        
        <div id="categoryNav" class="d-flex overflow-auto pb-2 mb-3"></div>
        <div id="menuContainer"></div>
    </div>

    <script>
        let fullMenu = [];

        async function loadMenu() {
            try {
                const res = await fetch('/api/menu');
                fullMenu = await res.json();
                renderCategoryNav();
                renderMenu(fullMenu);
            } catch(e) {
                console.error("Erreur de chargement", e);
            }
        }

        function renderCategoryNav() {
            const nav = document.getElementById('categoryNav');
            nav.innerHTML = '<button class="btn category-badge active" onclick="filterCat(\'all\', this)">Tous</button>';
            fullMenu.forEach(c => {
                nav.innerHTML += `<button class="btn category-badge" onclick="filterCat(${c.id}, this)">${c.category}</button>`;
            });
        }

        function filterCat(catId, btn) {
            document.querySelectorAll('.category-badge').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            if(catId === 'all') {
                renderMenu(fullMenu);
            } else {
                const filtered = fullMenu.filter(c => c.id === catId);
                renderMenu(filtered);
            }
        }

        function renderMenu(data) {
            const container = document.getElementById('menuContainer');
            container.innerHTML = '';
            
            data.forEach(cat => {
                let itemsHtml = '';
                cat.items.forEach(item => {
                    itemsHtml += `
                        <div class="menu-card ${!item.available ? 'out-of-stock' : ''}">
                            <div>
                                <span class="item-name">${item.name}</span>
                                ${!item.available ? '<br><span class="badge-rupture">Non disponible</span>' : ''}
                            </div>
                            <div class="item-price">${item.price > 0 ? item.price + ' DA' : '— DA'}</div>
                        </div>
                    `;
                });
                
                if(itemsHtml) {
                    container.innerHTML += `
                        <h4 class="text-warning mt-4 mb-3 border-bottom border-secondary pb-1">${cat.category}</h4>
                        ${itemsHtml}
                    `;
                }
            });
        }

        document.getElementById('searchInput').addEventListener('input', (e) => {
            const term = e.target.value.toLowerCase();
            const filtered = fullMenu.map(cat => ({
                ...cat,
                items: cat.items.filter(i => i.name.toLowerCase().includes(term))
            })).filter(cat => cat.items.length > 0);
            renderMenu(filtered);
        });

        loadMenu();
    </script>
</body>
</html>
"""

@app.route('/')
def client_view():
    return render_template_string(HTML_CLIENT)

init_db()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)