from flask import Flask, render_template, request, redirect, url_for, session, abort
import mysql.connector

app = Flask(__name__)
app.secret_key = 'some_secret_key'

# Database connection
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="ninewords"
)
cursor = db.cursor(dictionary=True)

# -------------------- ROUTES --------------------

@app.route('/')
def home():
    return render_template('syna.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/shop')
def shop_page():
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    return render_template('shop.html', products=products)


@app.route('/product/<int:product_id>')
def product_detail(product_id):
    cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
    product = cursor.fetchone()

    if product is None:
        abort(404)

    return render_template('product_detail.html', product=product)


# -------------------- CART --------------------

@app.route('/add_to_cart/<int:product_id>', methods=["POST"])
def add_to_cart(product_id):
    if "cart" not in session:
        session["cart"] = []

    cart = session["cart"]

    cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
    product = cursor.fetchone()

    if product:
        quantity = int(request.form.get("quantity", 1))
        size = request.form.get("size")

        # convert DB price safely (DECIMAL → float)
        price = float(product["price"])

        # check if already in cart (same id + size)
        existing_item = next(
            (item for item in cart if item["id"] == product_id and item["size"] == size),
            None
        )

        if existing_item:
            existing_item["quantity"] += quantity
        else:
            cart.append({
                "id": product["id"],
                "name": product["name"],
                "price": float(product["price"]),  # store as float ✅
                "image": product["image"],
                "description": product["description"],
                "quantity": quantity,
                "size": size
            })

    session["cart"] = cart
    return redirect(url_for("checkout"))


@app.route('/checkout')
def checkout():
    cart = session.get('cart', [])

    total = 0
    for item in cart:
        price = float(item.get("price", 0))  # safe access
        quantity = int(item.get("quantity", 1))
        total += price * quantity
    
    return render_template('checkout.html', cart=cart, total=total)


@app.route('/clear_cart')
def clear_cart():
    session.pop("cart", None)
    return redirect(url_for("shop_page"))


@app.route('/confirm', methods=["POST"])
def confirm_order():
    cart = session.get('cart', [])

    if not cart:
        return redirect(url_for("shop_page"))

    name = request.form.get("name")
    email = request.form.get("email")
    address = request.form.get("address")

    session.pop('cart', None)

    return render_template(
        'confirmation.html',
        name=name,
        email=email,
        address=address,
        cart=cart
    )


# -------------------- ERRORS --------------------

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404





# -------------------- RUN --------------------

if __name__ == "__main__":
    app.run(debug=False)