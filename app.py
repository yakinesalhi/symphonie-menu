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
        conn.execute('CREATE TABLE IF NOT EXISTS categories (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL, position INTEGER DEFAULT 0)')
        conn.execute('CREATE TABLE IF NOT EXISTS menu_items (id INTEGER PRIMARY KEY AUTOINCREMENT, category_id INTEGER, name TEXT NOT NULL, price REAL DEFAULT 0, available INTEGER DEFAULT 1, position INTEGER DEFAULT 0)')
        
        try:
            conn.execute('ALTER TABLE categories ADD COLUMN position INTEGER DEFAULT 0')
        except:
            pass
        try:
            conn.execute('ALTER TABLE menu_items ADD COLUMN position INTEGER DEFAULT 0')
        except:
            pass

        if conn.execute("SELECT COUNT(*) FROM categories").fetchone()[0] == 0:
            cats = [
                "Les Plats Gastro Volailles", "Viande Rouge", "Entrées Chaudes", 
                "Les Plats Traditionnels", "Nos Brochettes", "Pasta", 
                "Fast Food", "Nos Poissons", "Boissons Fraîches", 
                "Boissons Chaudes", "Desserts"
            ]
            for idx, c in enumerate(cats):
                conn.execute("INSERT INTO categories (name, position) VALUES (?, ?)", (c, idx))
            
            items_data = [
                # 1. Les Plats Gastro Volailles
                (1, 'Escalope de poulet grillée'), (1, 'Escalope à la crème'), (1, 'Escalope panée'), (1, 'Escalope milanaise'), 
                (1, 'Escalope borjaina'), (1, 'Kebab de volaille'), (1, 'Cordon bleu'), (1, 'Cuisse marinée'), (1, 'Cuisse panée'),
                
                # 2. Viande Rouge
                (2, 'Entrecôte de bœuf grillée'), (2, 'Entrecôte normande'), (2, 'Entrecôte chasseur'), (2, 'Entrecôte bordelaise'), 
                (2, 'Entrecôte sauce moutarde'), (2, 'Mix grillades'), (2, 'Filet sauce barbecue'), (2, 'Filet de bœuf'),
                
                # 3. Entrées Chaudes
                (3, 'Velouté de volaille'), (3, 'Soupe de poisson'), (3, 'Soupe de légumes'), (3, 'Chorba Frik'), (3, 'Hrira'), 
                (3, 'Pastilla'), (3, 'Bourek à la viande'), (3, 'Bourek au poulet'), (3, 'Brik Annabi à la viande'), (3, 'Brik Annabi au poulet'), 
                (3, 'Bourek aux crevettes'), (3, 'Omelette au choix'), (3, 'Omelette royale'), (3, 'Gratin de poulet'), (3, 'Gratin de viande'), 
                (3, 'Gratin de crevettes'), (3, 'Gratin mixte'), (3, 'Gratin de fruits de mer'),
                
                # 4. Les Plats Traditionnels
                (4, "Chakhchoukha de M'Sila"), (4, 'Chakhchoukha de Biskra'), (4, 'Trida de Constantine'), (4, 'Rechta'), 
                (4, 'Zviti'), (4, 'Couscous Traditionnel'), (4, 'Chtitha Lsan (Langue)'), (4, 'Chtitha Viande'), (4, 'Chtitha Moukh (Cervelle)'), (4, 'Douwara'), 
                (4, 'Tajine Zitoune'), (4, 'Jelbana'), (4, 'Mtouwem'), (4, 'Kebab Traditionnel'), (4, 'Ojja / Aaja'), (4, 'Les Abats'), 
                (4, 'Poulet Mfouwer (Vapeur)'), (4, 'Viande Mfouwer (Vapeur)'), (4, 'Bouzelouf'), (4, 'Méchoui (au poids)'), (4, 'Cuisse rôtie'),
                
                # 5. Nos Brochettes
                (5, 'Steak haché'), (5, 'Tranche de foie'), (5, 'Brochette de foie de dinde royale'), (5, 'Brochette merguez'), 
                (5, 'Brochette de viande royale'), (5, 'Brochette de foie de veau'), (5, 'Brochette Melfouf'), (5, 'Brochette Kebab'), 
                (5, "Brochette d'entrecôte de bœuf"), (5, "Côte d'agneau"), (5, 'Mélange Foie, Dinde & Viande'),
                
                # 6. Pasta
                (6, 'Spaghetti Bolognaise'), (6, 'Spaghetti Napolitaine'), (6, 'Spaghetti aux Fruits de Mer'), (6, 'Spaghetti Quatre Fromages'), 
                (6, 'Tagliatelles Poulet & Champignons'), (6, 'Tagliatelles Quatre Fromages'), (6, 'Tagliatelles au Saumon'), 
                (6, 'Tagliatelles au Camembert'), (6, 'Linguine aux Crevettes'),
                
                # 7. Fast Food
                (7, 'Tacos Poulet'), (7, 'Tacos Viande Hachée'), (7, 'Tacos Crispy'), (7, 'Tacos Mixte'), (7, 'Burger Poulet'), 
                (7, 'Burger Viande'), (7, 'Burger Mixte'), (7, 'Burger Crispy'), (7, 'Menu Enfant au Choix'),
                
                # 8. Nos Poissons
                (8, 'Dorade Grillée'), (8, 'Pavé de Saumon'), (8, 'Calamars Grillés / Frits'), (8, 'Loup de Mer'), (8, 'Seiche en Sauce'), (8, 'Steak d\'Espadon'), 
                (8, 'Crevettes Grillées'), (8, 'Crevettes Sautées en Sauce'), (8, 'Sardines Grillées'), (8, 'Rouget Frit / Grillé'), (8, 'Pageot'), (8, 'Marbré'), 
                (8, 'Brochet'), (8, 'Pagre'), (8, 'Plateau Mix Poissons'),
                
                # 9. Boissons Fraîches
                (9, 'Eau Minérale (Grand Modèle)'), (9, 'Eau Minérale (Petit Modèle)'), (9, 'Coca-Cola 1L'), (9, 'Hamoud Boualem 1L'), (9, 'Hamoud Canette'), (9, 'Coca-Cola Canette'), 
                (9, 'Eau de Source'), (9, "Jus d'Orange Naturel"), (9, 'Citronnade Naturelle'), (9, 'Mojito Maison (Sans alcool)'), (9, 'Cocktail de Fruits Frais'), 
                (9, 'Jus Signature Symphonie'), (9, 'Milkshake Gourmand'), (9, 'Café Glacé'), (9, 'Jus de Banane Frais'), (9, 'Jus de Fraise Frais'),
                
                # 10. Boissons Chaudes
                (10, 'Café Nespresso'), (10, 'Thé Traditionnel de Timimoun'), (10, 'Thé Lipton au Choix'), (10, 'Tisane Infusion Maison'),
                
                # 11. Desserts
                (11, 'Crêpe Simple (Sucre/Beurre)'), (11, 'Crêpe aux Fruits'), (11, 'Crêpe Surprise Symphonie'), (11, 'Crêpe Banane Chocolat'), (11, 'Crêpe Spéciale Maison'), 
                (11, 'Gaufre Simple'), (11, 'Gaufre aux Fruits'), (11, 'Gaufre Surprise'), (11, 'Gaufre Banane Chocolat'), (11, 'Fondant au Chocolat Coeur Coulant'), 
                (11, 'Mousse au Chocolat Noir'), (11, 'Crème Brûlée à la Vanille'), (11, 'Crème Caramel Onctueuse'), (11, 'Tiramisu Italien Traditionnel'), (11, 'Salade de Fruits Frais'), 
                (11, 'Assiette de Fruits de Saison')
            ]
            
            for idx, (cat_id, name) in enumerate(items_data):
                conn.execute("INSERT INTO menu_items (category_id, name, price, position) VALUES (?, ?, 0, ?)", (cat_id, name, idx))
            
            conn.commit()
        conn.close()
    except Exception as e:
        print(f"Erreur DB init: {e}")

init_db()

# --- SÉCURITÉ ADMIN ---
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')

def check_auth(username, password):
    return username == ADMIN_USERNAME and password == ADMIN_PASSWORD

def check_auth(username, password):
    # Si les variables d'environnement sont absentes sur le serveur, bloque tout accès
    if not ADMIN_USERNAME or not ADMIN_PASSWORD:
        return False
    return username == ADMIN_USERNAME and password == ADMIN_PASSWORD

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

# --- API ROUTES ---
@app.route('/api/menu')
def get_menu():
    try:
        conn = get_db()
        cats = conn.execute("SELECT * FROM categories ORDER BY position ASC, id ASC").fetchall()
        result = []
        for cat in cats:
            items = conn.execute("SELECT * FROM menu_items WHERE category_id = ? ORDER BY position ASC, id ASC", (cat['id'],)).fetchall()
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
@requires_auth
def add_category():
    name = request.json.get('name')
    conn = get_db()
    try:
        max_pos = conn.execute("SELECT MAX(position) FROM categories").fetchone()[0] or 0
        conn.execute("INSERT INTO categories (name, position) VALUES (?, ?)", (name, max_pos + 1))
        conn.commit()
    except:
        pass
    conn.close()
    return jsonify({'success': True})

@app.route('/api/categories/<int:id>', methods=['PUT'])
@requires_auth
def update_category(id):
    name = request.json.get('name')
    conn = get_db()
    conn.execute("UPDATE categories SET name = ? WHERE id = ?", (name, id))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/categories/<int:id>', methods=['DELETE'])
@requires_auth
def delete_category(id):
    conn = get_db()
    conn.execute("DELETE FROM menu_items WHERE category_id = ?", (id,))
    conn.execute("DELETE FROM categories WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/categories/<int:id>/move/<string:direction>', methods=['POST'])
@requires_auth
def move_category(id, direction):
    conn = get_db()
    cats = conn.execute("SELECT id, position FROM categories ORDER BY position ASC, id ASC").fetchall()
    cats = [dict(c) for c in cats]
    idx = next((i for i, c in enumerate(cats) if c['id'] == id), None)
    
    if idx is not None:
        target_idx = idx - 1 if direction == 'up' else idx + 1
        if 0 <= target_idx < len(cats):
            conn.execute("UPDATE categories SET position = ? WHERE id = ?", (cats[target_idx]['position'], cats[idx]['id']))
            conn.execute("UPDATE categories SET position = ? WHERE id = ?", (cats[idx]['position'], cats[target_idx]['id']))
            conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/items', methods=['POST'])
@requires_auth
def add_item():
    data = request.json
    conn = get_db()
    max_pos = conn.execute("SELECT MAX(position) FROM menu_items WHERE category_id = ?", (data['category_id'],)).fetchone()[0] or 0
    conn.execute("INSERT INTO menu_items (category_id, name, price, position) VALUES (?, ?, ?, ?)", 
                 (data['category_id'], data['name'], data['price'], max_pos + 1))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/items/<int:id>', methods=['PUT'])
@requires_auth
def update_item(id):
    data = request.json
    conn = get_db()
    conn.execute("UPDATE menu_items SET name = ?, price = ? WHERE id = ?", (data['name'], data['price'], id))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/items/<int:id>', methods=['DELETE'])
@requires_auth
def delete_item(id):
    conn = get_db()
    conn.execute("DELETE FROM menu_items WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/items/<int:id>/move/<string:direction>', methods=['POST'])
@requires_auth
def move_item(id, direction):
    conn = get_db()
    item = conn.execute("SELECT category_id FROM menu_items WHERE id = ?", (id,)).fetchone()
    if item:
        cat_id = item['category_id']
        items = conn.execute("SELECT id, position FROM menu_items WHERE category_id = ? ORDER BY position ASC, id ASC", (cat_id,)).fetchall()
        items = [dict(i) for i in items]
        idx = next((i for i, elem in enumerate(items) if elem['id'] == id), None)
        if idx is not None:
            target_idx = idx - 1 if direction == 'up' else idx + 1
            if 0 <= target_idx < len(items):
                conn.execute("UPDATE menu_items SET position = ? WHERE id = ?", (items[target_idx]['position'], items[idx]['id']))
                conn.execute("UPDATE menu_items SET position = ? WHERE id = ?", (items[idx]['position'], items[target_idx]['id']))
                conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/toggle/<int:id>', methods=['POST'])
@requires_auth
def toggle_item(id):
    conn = get_db()
    conn.execute("UPDATE menu_items SET available = CASE WHEN available = 1 THEN 0 ELSE 1 END WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

# --- TEMPLATES UI ---
HTML_CLIENT = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>خيمة السمفونية | Symphonie Restaurant</title>
    <link href="https://fonts.googleapis.com/css2?family=Amiri:ital,wght@0,400;0,700;1,400&family=Cormorant+Garamond:ital,wght@0,500;0,600;0,700;1,400&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        :root {
            --gold-primary: #d4af37;
            --gold-light: #f3e5ab;
            --gold-gradient: linear-gradient(135deg, #f3e5ab 0%, #d4af37 50%, #aa7c11 100%);
            --bg-dark: #0a0a0a;
            --card-bg: rgba(20, 20, 20, 0.85);
            --border-gold: rgba(212, 175, 55, 0.25);
        }
        body { 
            background-color: var(--bg-dark); 
            color: #f0f0f0; 
            font-family: 'Plus Jakarta Sans', sans-serif; 
            padding-bottom: 50px;
            background-image: radial-gradient(circle at 50% 0%, #1a1408 0%, #0a0a0a 80%);
            background-attachment: fixed;
        }
        .hero { 
            text-align: center; 
            padding: 45px 20px 25px; 
            background: linear-gradient(180deg, rgba(30,23,10,0.85) 0%, rgba(10,10,10,0) 100%);
            border-bottom: 1px solid var(--border-gold); 
            position: relative;
        }
        .royal-crest {
            font-size: 2rem;
            background: var(--gold-gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 5px;
        }
        .brand-title-ar { 
            font-family: 'Amiri', serif;
            color: var(--gold-primary); 
            font-size: 2.9rem; 
            font-weight: 700; 
            line-height: 1.2;
            text-shadow: 0 2px 10px rgba(212, 175, 55, 0.2);
            margin-bottom: 0;
        }
        .brand-subtitle { 
            font-family: 'Cormorant Garamond', serif;
            color: var(--gold-light); 
            font-size: 1.25rem; 
            letter-spacing: 4px;
            text-transform: uppercase;
            font-weight: 600;
            margin-top: 5px;
        }
        .gold-divider {
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 15px auto 5px;
            width: 50%;
            max-width: 200px;
        }
        .gold-divider::before, .gold-divider::after {
            content: '';
            flex: 1;
            border-bottom: 1px solid var(--border-gold);
        }
        .gold-divider i {
            color: var(--gold-primary);
            padding: 0 10px;
            font-size: 0.75rem;
        }
        .search-box { 
            background: rgba(20, 20, 20, 0.8); 
            border: 1px solid var(--border-gold); 
            color: #ffffff; 
            border-radius: 30px; 
            padding: 12px 25px; 
            backdrop-filter: blur(10px);
            font-size: 0.95rem;
            transition: all 0.3s ease;
        }
        .search-box:focus { 
            background: rgba(30, 30, 30, 0.95); 
            color: #ffffff; 
            border-color: var(--gold-primary); 
            box-shadow: 0 0 15px rgba(212, 175, 55, 0.3); 
        }
        .category-nav { scrollbar-width: none; }
        .category-nav::-webkit-scrollbar { display: none; }
        .category-badge { 
            background: rgba(25, 25, 25, 0.7); 
            color: #d0d0d0; 
            border: 1px solid var(--border-gold); 
            margin: 4px; 
            border-radius: 4px; 
            padding: 5px 12px;
            font-family: 'Cormorant Garamond', serif;
            font-size: 0.95rem; 
            font-weight: 600;
            letter-spacing: 1px;
            text-transform: uppercase;
            white-space: nowrap;
            transition: all 0.3s ease;
            backdrop-filter: blur(5px);
        }
        .category-badge.active { 
            background: var(--gold-gradient); 
            color: #0a0a0a; 
            font-weight: 700; 
            border-color: var(--gold-primary);
            box-shadow: 0 4px 15px rgba(212, 175, 55, 0.25);
        }
        .section-header {
            font-family: 'Cormorant Garamond', serif;
            color: var(--gold-primary);
            font-size: 1.85rem;
            font-weight: 700;
            letter-spacing: 2px;
            text-transform: uppercase;
            text-align: center;
            margin-top: 40px;
            margin-bottom: 22px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 15px;
        }
        .section-header::before, .section-header::after {
            content: '';
            flex: 1;
            border-bottom: 1px solid var(--border-gold);
            opacity: 0.5;
        }
        .gold-symbol {
            font-size: 0.85rem;
            color: var(--gold-light);
            vertical-align: middle;
        }
        .menu-card { 
            background: var(--card-bg); 
            border: 1px solid rgba(255, 255, 255, 0.05); 
            border-left: 3px solid var(--gold-primary);
            border-radius: 8px; 
            margin-bottom: 12px; 
            padding: 16px 20px; 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
            backdrop-filter: blur(10px);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .menu-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 15px rgba(0, 0, 0, 0.5);
            border-color: var(--border-gold);
        }
        .item-name { 
            font-size: 1.05rem; 
            color: #ffffff; 
            font-weight: 500; 
            letter-spacing: 0.3px;
        }
        .item-price { 
            font-family: 'Cormorant Garamond', serif;
            font-size: 1.35rem; 
            color: var(--gold-primary); 
            font-weight: 700; 
            white-space: nowrap;
            margin-left: 15px;
        }
        .out-of-stock { opacity: 0.45; filter: grayscale(80%); }
        .badge-rupture { 
            background-color: rgba(220, 53, 69, 0.15); 
            color: #ff6b6b; 
            border: 1px solid rgba(220, 53, 69, 0.4);
            font-size: 0.7rem; 
            padding: 2px 8px; 
            border-radius: 4px; 
            display: inline-block;
            margin-top: 4px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .footer-brand {
            text-align: center;
            margin-top: 50px;
            padding-top: 25px;
            border-top: 1px solid var(--border-gold);
            color: #777;
            font-size: 0.85rem;
        }
    </style>
</head>
<body>
    <div class="hero">
        <div class="royal-crest"><i class="fas fa-crown"></i></div>
        <h1 class="brand-title-ar">خيمة السمفونية</h1>
        <div class="brand-subtitle">Symphonie Restaurant</div>
        <div class="gold-divider"><i class="fas fa-star"></i></div>
    </div>

    <div class="container py-3" style="max-width: 720px;">
        <div id="categoryNav" class="d-flex overflow-auto pb-2 mb-3 category-nav"></div>
        <div id="menuContainer"><div class="text-center text-warning mt-5"><i class="fas fa-spinner fa-spin fa-2x mb-3"></i><br>Chargement du menu...</div></div>
        
        <div class="footer-brand">
            <p class="m-0"></p>
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
                document.getElementById('menuContainer').innerHTML = '<div class="text-center text-danger mt-5">Erreur de chargement du menu.</div>';
            }
        }

        function renderNav() {
            const nav = document.getElementById('categoryNav');
            nav.innerHTML = `<button class="btn category-badge active" onclick="filterCat('all', this)">Tous</button>`;
            fullMenu.forEach(c => {
                if(c.items.length > 0) {
                    nav.innerHTML += `<button class="btn category-badge" onclick="filterCat(${c.id}, this)">${c.category}</button>`;
                }
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
                let html = `
                    <div class="section-header">
                        <span class="gold-symbol">✦</span>
                        <span>${cat.category}</span>
                        <span class="gold-symbol">✦</span>
                    </div>`;
                cat.items.forEach(item => {
                    html += `
                        <div class="menu-card ${!item.available ? 'out-of-stock' : ''}">
                            <div>
                                <div class="item-name">${item.name}</div>
                                ${!item.available ? '<span class="badge-rupture"><i class="fas fa-times-circle"></i> Indisponible</span>' : ''}
                            </div>
                            <div class="item-price">${item.price > 0 ? item.price + ' <small style="font-size: 0.8rem;">DA</small>' : '—'}</div>
                        </div>`;
                });
                container.innerHTML += html;
            });
        }

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
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Sortable/1.15.0/Sortable.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <style>
        body { background: #f4f6f9; padding-bottom: 60px; font-family: 'Segoe UI', sans-serif; }
        .admin-header { background: #1a160d; color: #d4af37; padding: 30px; border-bottom: 3px solid #d4af37; margin-bottom: 25px; }
        .card { border: none; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.06); margin-bottom: 20px; overflow: hidden; }
        .item-row { display: flex; justify-content: space-between; align-items: center; padding: 10px 15px; border-bottom: 1px solid #f0f0f0; background: white;}
        .item-row:hover { background: #fdfdfd; }
        .controls-group { display: flex; align-items: center; gap: 6px; }
        .btn-move { padding: 2px 8px; font-size: 0.8rem; }
    </style>
</head>
<body>
    <div class="admin-header">
    <div class="container d-flex justify-content-between align-items-center" style="max-width: 950px;">
        <div>
            <h3 class="m-0 text-warning fw-bold"><i class="fas fa-sliders"></i> Espace Gérant - Symphonie</h3>
        </div>
        <div class="d-flex gap-2">
            <!-- Bouton 1 : Téléchargement direct du QR Code -->
            <a href="/admin/download-qrcode" class="btn btn-warning btn-sm fw-bold d-flex align-items-center gap-2 px-3">
                <i class="fas fa-qrcode"></i> Télécharger QR Code
            </a>
        </div>
    </div>
</div>

    <div class="container" style="max-width: 950px;">
        <div class="row mb-4">
            <div class="col-md-6 mb-3">
                <div class="card h-100"><div class="card-body">
                    <h6 class="text-primary fw-bold"><i class="fas fa-folder-plus"></i> Nouvelle Catégorie</h6>
                    <div class="d-flex gap-2 mt-3">
                        <input type="text" id="newCatName" class="form-control" placeholder="Nom de la catégorie">
                        <button class="btn btn-primary px-3" onclick="addCategory()">Ajouter</button>
                    </div>
                </div></div>
            </div>
            <div class="col-md-6 mb-3">
                <div class="card h-100"><div class="card-body">
                    <h6 class="text-success fw-bold"><i class="fas fa-plus-circle"></i> Nouveau Plat</h6>
                    <div class="d-flex gap-2 flex-wrap mt-3">
                        <select id="newItemCat" class="form-select w-100"></select>
                        <input type="text" id="newItemName" class="form-control" placeholder="Nom du plat" style="flex: 2;">
                        <input type="number" id="newItemPrice" class="form-control" placeholder="Prix (DA)" style="flex: 1;">
                        <button class="btn btn-success px-3" onclick="addItem()">Ajouter</button>
                    </div>
                </div></div>
            </div>
        </div>

        <h5 class="mb-3 text-secondary border-bottom pb-2"><i class="fas fa-list-check"></i> Gestion du Menu </h5>
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

    fullMenu.forEach((cat) => {
        let html = `
        <div class="card mb-3 cat-card" data-id="${cat.id}">
            <div class="bg-dark text-white p-3 d-flex justify-content-between align-items-center">
                <div class="d-flex align-items-center gap-2">
                    <!-- Poignée de glissement pour la catégorie -->
                    <i class="fas fa-grip-vertical text-warning opacity-75 drag-handle-cat me-2" style="cursor: grab; font-size: 1.2rem;"></i>
                    <input type="text" class="form-control form-control-sm bg-transparent text-warning fw-bold border-0" value="${cat.category}" onchange="updateCategory(${cat.id}, this.value)" style="font-size: 1.3rem; width: 340px;">
                </div>
                <button class="btn btn-sm btn-outline-danger" onclick="deleteCategory(${cat.id})"><i class="fas fa-trash"></i></button>
            </div>
            <div class="items-container" data-catid="${cat.id}">`;

        if(cat.items.length === 0) {
            html += `<div class="p-3 text-center text-muted">Aucun plat dans cette catégorie (masquée côté client).</div>`;
        } else {
            cat.items.forEach((item) => {
                html += `
                <div class="item-row d-flex justify-content-between align-items-center p-2 border-bottom bg-white" data-id="${item.id}">
                    <div class="d-flex align-items-center gap-2" style="flex: 1;">
                        <!-- Poignée de glissement pour le plat -->
                        <i class="fas fa-grip-lines text-muted drag-handle-item me-2" style="cursor: grab;"></i>
                        <input type="text" class="form-control form-control-sm border-0 fw-semibold" value="${item.name}" onchange="updateItem(${item.id}, this.value, ${item.price})" style="max-width: 420px; font-size: 1.15rem;">
                    </div>
                    <div class="controls-group d-flex align-items-center gap-2">
                        <input type="number" class="form-control form-control-sm text-center fw-bold" style="width: 95px; font-size: 1.05rem;" value="${item.price}" onchange="updateItem(${item.id}, null, this.value)">
                        <span class="text-muted" style="font-size: 0.85rem;">DA</span>
                        <button class="btn btn-sm ${item.available ? 'btn-success' : 'btn-secondary'}" onclick="toggle(${item.id})" style="width: 85px;">
                            ${item.available ? 'En Stock' : 'Rupture'}
                        </button>
                        <button class="btn btn-sm btn-outline-danger" onclick="deleteItem(${item.id})"><i class="fas fa-trash"></i></button>
                    </div>
                </div>`;
            });
        }
        html += `</div></div>`;
        container.innerHTML += html;
    });

    // Activer le glisser-déposer sur les catégories
    new Sortable(container, {
        handle: '.drag-handle-cat',
        animation: 150
    });

    // Activer le glisser-déposer sur les plats à l'intérieur de chaque catégorie
    document.querySelectorAll('.items-container').forEach(el => {
        new Sortable(el, {
            handle: '.drag-handle-item',
            animation: 150
        });
    });
}

        async function addCategory() {
            const name = document.getElementById('newCatName').value;
            if(!name) return;
            await fetch('/api/categories', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({name})});
            document.getElementById('newCatName').value = '';
            loadData();
        }

        async function updateCategory(id, name) {
            await fetch(`/api/categories/${id}`, {method: 'PUT', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({name})});
        }

        async function moveCategory(id, direction) {
            await fetch(`/api/categories/${id}/move/${direction}`, {method: 'POST'});
            loadData();
        }

        async function deleteCategory(id) {
            if(confirm("Supprimer cette catégorie et tous ses plats ?")) {
                await fetch(`/api/categories/${id}`, {method: 'DELETE'});
                loadData();
            }
        }

        async function addItem() {
            const category_id = document.getElementById('newItemCat').value;
            const name = document.getElementById('newItemName').value;
            const price = document.getElementById('newItemPrice').value;
            if(!category_id || !name) return alert("Saisissez un nom et choisissez une catégorie.");
            await fetch('/api/items', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({category_id, name, price: parseFloat(price||0)})});
            document.getElementById('newItemName').value = '';
            document.getElementById('newItemPrice').value = '';
            loadData();
        }

        async function updateItem(id, nameInput, priceInput) {
            const item = fullMenu.flatMap(c => c.items).find(i => i.id === id);
            const newName = nameInput !== null ? nameInput : item.name;
            const newPrice = priceInput !== null ? parseFloat(priceInput) : item.price;
            await fetch(`/api/items/${id}`, {method: 'PUT', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({name: newName, price: newPrice})});
        }

        async function moveItem(id, direction) {
            await fetch(`/api/items/${id}/move/${direction}`, {method: 'POST'});
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
    port = int(os.environ.get('PORT', 5002))
    app.run(host='0.0.0.0', port=port, debug=False)