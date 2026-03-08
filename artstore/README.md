# artstore

A minimal Flask storefront for art & merch drops.

## Features
- Product listing page with grid layout
- Add to cart (session-based)
- Checkout summary with order confirmation
- Admin panel to add/remove products

## Setup

```bash
pip install flask
python app.py
```

Then open:
- **Store** → http://localhost:5000
- **Admin** → http://localhost:5000/admin `(password: admin123)`

## Project Structure

```
artstore/
├── app.py              # Flask routes & database logic
├── requirements.txt
├── static/
│   └── style.css       # Dark art gallery aesthetic
└── templates/
    ├── base.html        # Shared nav, flash messages, footer
    ├── index.html       # Product grid
    ├── cart.html        # Cart view
    ├── checkout.html    # Checkout form
    ├── confirmed.html   # Order confirmation
    ├── admin_login.html
    └── admin_dashboard.html
```

## What You'll Learn
- Flask routing (`@app.route`)
- Jinja2 templating (loops, conditionals, template inheritance)
- SQLite with Python (`sqlite3`)
- Session-based state (cart persists across pages)
- HTML forms with POST requests

## Next Steps
- Add quantity controls in the cart
- Add product image uploads (instead of URLs)
- Add real payment via Stripe
- Add user accounts/login
- Deploy to Railway or Render
