"""
artstore — A minimal Flask storefront for art & merch.

Run:
  pip install flask
  python app.py

Then open: http://localhost:5000
Admin:     http://localhost:5000/admin  (password: admin123)
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "artstore_secret_change_this"

DB = "store.db"
ADMIN_PASSWORD = "admin123"

# ── DATABASE ─────────────────────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row  # lets us access columns by name
    return conn

def init_db():
    """Create tables and seed with sample products on first run."""
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            description TEXT,
            price       REAL    NOT NULL,
            image_url   TEXT    DEFAULT '',
            stock       INTEGER DEFAULT 10
        )
    """)
    # Only seed if the table is empty
    count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    if count == 0:
        seed = [
            ("Caelum City Print",     "Limited edition giclée print. 18×24 inches, signed.",   45.00, "https://placehold.co/400x400/111/eee?text=Print",   15),
            ("HOLLOW Logo Tee",        "Black heavyweight tee. Screen printed. Sizes S–XL.",    35.00, "https://placehold.co/400x400/111/eee?text=Tee",     20),
            ("Dex Marlow Patch",       "Embroidered iron-on patch. 3 inches wide.",             12.00, "https://placehold.co/400x400/111/eee?text=Patch",   50),
            ("Ash & Neon Hoodie",      "Pullover hoodie, ash grey with risograph neon print.",  65.00, "https://placehold.co/400x400/111/eee?text=Hoodie",  12),
            ("Ghost Lattice Poster",   "Operation codename poster. Two-colour risograph.",      25.00, "https://placehold.co/400x400/111/eee?text=Poster",  30),
            ("Caelum Enamel Pin",      "Hard enamel pin with black nickel finish. 1.5 inches.", 14.00, "https://placehold.co/400x400/111/eee?text=Pin",     40),
        ]
        conn.executemany(
            "INSERT INTO products (name, description, price, image_url, stock) VALUES (?,?,?,?,?)",
            seed
        )
    conn.commit()
    conn.close()

# ── CART HELPERS ─────────────────────────────────────────────────────────────

def get_cart():
    """Return the cart dict from the session. {product_id: quantity}"""
    return session.get("cart", {})

def cart_count():
    """Total number of items in the cart."""
    return sum(get_cart().values())

def cart_total(conn):
    """Calculate total price of all cart items."""
    cart = get_cart()
    if not cart:
        return 0
    total = 0
    for pid, qty in cart.items():
        row = conn.execute("SELECT price FROM products WHERE id = ?", (pid,)).fetchone()
        if row:
            total += row["price"] * qty
    return total

# ── ROUTES: STOREFRONT ───────────────────────────────────────────────────────

@app.route("/")
def index():
    """Homepage with carousel."""
    return render_template("index.html", cart_count=cart_count())

@app.route("/products")
def products():
    """Product listing page."""
    conn = get_db()
    products = conn.execute("SELECT * FROM products").fetchall()
    conn.close()
    return render_template("products.html", products=products, cart_count=cart_count())

@app.route("/cart")
def cart():
    """View current cart."""
    conn = get_db()
    cart = get_cart()
    items = []
    for pid, qty in cart.items():
        row = conn.execute("SELECT * FROM products WHERE id = ?", (pid,)).fetchone()
        if row:
            items.append({"product": row, "qty": qty, "subtotal": row["price"] * qty})
    total = cart_total(conn)
    conn.close()
    return render_template("cart.html", items=items, total=total, cart_count=cart_count())

@app.route("/add/<int:product_id>", methods=["POST"])
def add_to_cart(product_id):
    """Add one unit of a product to the cart."""
    cart = get_cart()
    pid = str(product_id)
    cart[pid] = cart.get(pid, 0) + 1
    session["cart"] = cart
    flash("Added to cart.", "success")
    return redirect(url_for("products"))

@app.route("/remove/<int:product_id>", methods=["POST"])
def remove_from_cart(product_id):
    """Remove a product from the cart entirely."""
    cart = get_cart()
    pid = str(product_id)
    cart.pop(pid, None)
    session["cart"] = cart
    return redirect(url_for("cart"))

@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    """Checkout summary — collect name/email, confirm order."""
    conn = get_db()
    cart = get_cart()

    if not cart:
        flash("Your cart is empty.", "error")
        return redirect(url_for("index"))

    items = []
    for pid, qty in cart.items():
        row = conn.execute("SELECT * FROM products WHERE id = ?", (pid,)).fetchone()
        if row:
            items.append({"product": row, "qty": qty, "subtotal": row["price"] * qty})
    total = cart_total(conn)
    conn.close()

    if request.method == "POST":
        name  = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        if not name or not email:
            flash("Please fill in all fields.", "error")
        else:
            # In a real app: save the order, charge the card, etc.
            session["cart"] = {}
            session["last_order"] = {"name": name, "email": email, "total": total}
            return redirect(url_for("order_confirmed"))

    return render_template("checkout.html", items=items, total=total, cart_count=cart_count())

@app.route("/order-confirmed")
def order_confirmed():
    order = session.pop("last_order", None)
    if not order:
        return redirect(url_for("index"))
    return render_template("confirmed.html", order=order, cart_count=0)

# ── ROUTES: ADMIN ─────────────────────────────────────────────────────────────

@app.route("/admin", methods=["GET", "POST"])
def admin():
    """Admin login gate."""
    if session.get("admin"):
        return redirect(url_for("admin_dashboard"))
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect(url_for("admin_dashboard"))
        flash("Wrong password.", "error")
    return render_template("admin_login.html", cart_count=0)

@app.route("/admin/dashboard")
def admin_dashboard():
    if not session.get("admin"):
        return redirect(url_for("admin"))
    conn = get_db()
    products = conn.execute("SELECT * FROM products").fetchall()
    conn.close()
    return render_template("admin_dashboard.html", products=products, cart_count=0)

@app.route("/admin/add", methods=["POST"])
def admin_add():
    if not session.get("admin"):
        return redirect(url_for("admin"))
    name        = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()
    price       = float(request.form.get("price", 0))
    stock       = int(request.form.get("stock", 10))
    image_url   = request.form.get("image_url", "").strip()
    if name and price > 0:
        conn = get_db()
        conn.execute(
            "INSERT INTO products (name, description, price, stock, image_url) VALUES (?,?,?,?,?)",
            (name, description, price, stock, image_url)
        )
        conn.commit()
        conn.close()
        flash(f"'{name}' added.", "success")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/delete/<int:product_id>", methods=["POST"])
def admin_delete(product_id):
    if not session.get("admin"):
        return redirect(url_for("admin"))
    conn = get_db()
    conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()
    flash("Product removed.", "success")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/edit/<int:product_id>", methods=["GET", "POST"])
def admin_edit(product_id):
    if not session.get("admin"):
        return redirect(url_for("admin"))
    conn = get_db()
    product = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    if not product:
        conn.close()
        flash("Product not found.", "error")
        return redirect(url_for("admin_dashboard"))
    
    if request.method == "POST":
        name        = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        price       = float(request.form.get("price", 0))
        stock       = int(request.form.get("stock", 10))
        image_url   = request.form.get("image_url", "").strip()
        if name and price > 0:
            conn.execute(
                "UPDATE products SET name = ?, description = ?, price = ?, stock = ?, image_url = ? WHERE id = ?",
                (name, description, price, stock, image_url, product_id)
            )
            conn.commit()
            flash(f"'{name}' updated.", "success")
            conn.close()
            return redirect(url_for("admin_dashboard"))
        else:
            flash("Invalid data.", "error")
    
    conn.close()
    return render_template("admin_edit.html", product=product, cart_count=0)

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("index"))

# ── ENTRY ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    init_db()
    print("\n  🎨 artstore running at http://localhost:8000")
    print("  📱 Network access at http://172.20.10.3:8000")
    print("  🔐 Admin panel at  http://localhost:8000/admin  (password: admin123)\n")
    app.run(host='0.0.0.0', port=8000, debug=True)
