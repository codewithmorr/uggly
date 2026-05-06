

from flask import Flask, render_template, request, redirect, url_for, session, abort
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash

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
db.ping(reconnect=True)
# -------------------- ROUTES --------------------

@app.route('/')
def home():
    return render_template('syna.html')




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
# user routes
# user registration
@app.route('/register', methods = ["GET", "POST"])
def register():
    if request.method =="POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
# hash the password before storage
        hashed_password = generate_password_hash(password)

        cursor.execute("""
            INSERT INTO users(username, email, password) VALUES(%s, %s, %s)
        """, (username, email, hashed_password))
        db.commit()

        return redirect(url_for("login"))
    return render_template("register.html")



# user login

@app.route('/login', methods= ["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()


        if user and check_password_hash(user["password"],password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("home"))
        else:
            return "invalid login", 403 
    return render_template("login.html")

#user logout
@app.route('/logout') 
def logout():
    session.pop("user_id", None)
    session.pop("username", None)
    return redirect(url_for("home"))

#user profile
@app.route('/profile')
def profile():
    if not session.get("user_id"):
        return redirect(url_for("login"))
    user_id = session["user_id"]

    # user information
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    #get user orders
    cursor.execute("SELECT * FROM orders WHERE user_id = %s",
     (user_id,))
    orders = cursor.fetchall()

    total_spent = sum(float(o["total"]) for o in orders)

    return render_template("profile.html", user=user, orders=orders, total_spent=total_spent)

# order details
@app.route('/order/<int:order_id>')
def order_detail(order_id):
    if not session.get("user_id"):
        return redirect(url_for("login"))

    # get order
    cursor.execute("SELECT * FROM orders WHERE id = %s", (order_id,))
    order = cursor.fetchone()

    # get items
    cursor.execute("SELECT * FROM order_items WHERE order_id = %s", (order_id,))
    items = cursor.fetchall()
    return render_template("order_detail.html", order=order, items=items)


@app.route('/profile/edit', methods=["GET", "POST"])
def edit_profile():
    if not session.get("user_id"):
        return redirect(url_for("login"))
    user_id = session["user_id"]


    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")

        cursor.execute("""
                       UPDATE users 
                       SET username = %s , email = %s
                       WHERE id = %s
                       """, (username, email, user_id))
        db.commit()
        session["username"] = username
        return redirect(url_for("profile"))
    
    cursor.execute("SELECT *FROM users WHERE  id =%s", (user_id,))
    user = cursor.fetchone()

    return render_template("edit_profile.html", user=user)


# admin CRUD routes
@app.route('/admin/login', methods=["GET","POST"])
def admin_login():
    if request.method =="POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username =="HUSH&BLUSH" and password =="within":
            session["admin"] = True
            return redirect(url_for("admin_dashboard"))
        else:
            return "employees only", 403
    return render_template("admin_login.html")


# admin logout
@app.route('/admin/logout')
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("home"))

# admin helper and protection

def is_admin():
    return session.get("admin")

# read ADMIN DASHBOARD
@app.route('/admin')
def admin_dashboard():
    if not is_admin():
        abort(403)

    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    # total units sold
    total_sold = sum(p["sold"] for p in products)

    # total product revenue
    total_revenue = sum(p["sold"] * float(p["price"]) for p in products)

    total_products = len(products)
    low_stock = [p for p in products if p["stock"] < 5]

    return render_template('admin_dashboard.html', products=products, 
    total_sold=total_sold, total_revenue=total_revenue, total_products=total_products, 
    low_stock=low_stock)

# addproduct 
@app.route('/admin/add', methods =["GET", "POST"])
def admin_add():
    if not is_admin():
        return redirect(url_for("admin_login"))
    
    if request.method == "POST":
        name = request.form.get('name')
        price = request.form.get('price')
        image = request.form.get('image')
        description = request.form.get('description')
        stock = request.form.get('stock')

        cursor.execute(
           "INSERT INTO products(name, price,  image, description, stock) VALUES(%s , %s , %s , %s , %s)",
           (name, price, image, description, stock)
       )
        db.commit()

        return redirect(url_for("admin_dashboard"))
    
    return render_template("admin_add.html")

# update product
@app.route('/admin/edit/<int:product_id>', methods=["GET", "POST"])
def admin_edit(product_id):
    if not is_admin():
        return redirect(url_for("admin_login"))

    cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
    product = cursor.fetchone()

    if request.method == "POST":
        name = request.form.get('name')
        price = request.form.get('price')
        image = request.form.get('image')
        stock = request.form.get('stock')
        description = request.form.get('description')

        cursor.execute(
            "UPDATE products SET name=%s, price=%s, image=%s, stock=%s, description=%s WHERE id=%s",
            (name, price, image, stock, description, product_id)
        )
        db.commit()

        return redirect(url_for("admin_dashboard"))

    return render_template("admin_edit.html", product=product)

# delete product
@app.route('/admin/delete/<int:product_id>', methods=["POST"])
def admin_delete(product_id):
    if not is_admin():
        return redirect(url_for("admin_login"))
    
    cursor.execute("DELETE FROM products WHERE id = %s", (product_id,))
    db.commit()

    return redirect(url_for("admin_dashboard"))

# admin user view
@app.route('/admin/users')
def admin_users():
    if not is_admin():
        abort(403)

    cursor.execute("SELECT *FROM users")
    users = cursor.fetchall()

    return render_template("admin_users.html", users=users)

# -------------------- CART --------------------

@app.route('/add_to_cart/<int:product_id>', methods=["POST"])
def add_to_cart(product_id):
    if "cart" not in session:
        session["cart"] = []

    cart = session["cart"]

    cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
    product = cursor.fetchone()

    if not product:
        return redirect(url_for("shop_page"))

    quantity = int(request.form.get("quantity", 1))
    size = request.form.get("size")

    # stock control
    if quantity > product["stock"]:
        return render_template("product_detail.html",
                               product=product,
                               error="Order cannot be placed - not enough stock available")

    # convert DB price safely (DECIMAL → float)
    price = float(product["price"])

    # check if already in cart (same id + size)
    existing_item = next(
        (item for item in cart if item["id"] == product_id and item["size"] == size),
        None
    )

    existing_qty = existing_item["quantity"] if existing_item else 0
    new_total_qty = existing_qty + quantity

    if new_total_qty > product["stock"]:
        return render_template("product_detail.html",
                               product = product,
                               error=f"Only{product['stock']} available in stock")
    if existing_item:
        existing_item["quantity"] = new_total_qty
    else:
        cart.append({
            "id": product["id"],
            "name": product["name"],
            "price": float(product["price"]),
            "image": product["image"],
                "description": product["description"],
                "quantity": quantity,
                "stock": product["stock"]
            })

    session["cart"] = cart
    return redirect(url_for("checkout"))
@app.route('/cart/increase/<int:product_id>')
def increase_cart(product_id):
    cart = session.get("cart",[])

    for item in cart:
        if item["id"] == product_id:
            item["quantity"]+=1


            # stop increasing if it exceeds stock
            if item["quantity"] > item["stock"]:
                return redirect(url_for("checkout"))
            break
    session["cart"] = cart
    return redirect(url_for("checkout"))
# decrease item quantity in cart
@app.route('/cart/decrease/<int:product_id>')
def decrease_cart(product_id):
    cart = session.get("cart",[])

    for item in cart:
        if item["id"] == product_id:
            if item["quantity"] > 1:
                item["quantity"]-=1
            else:
                cart.remove(item)
            break
    session["cart"] = cart
    return redirect(url_for("checkout"))

@app.route('/cart/remove/<int:product_id>')
def remove_from_cart(product_id):
    cart = session.get("cart",[])

    cart = [
        item for item in cart
        if not (item["id"] == product_id)
    ]
    session["cart"] = cart
    return redirect(url_for("checkout"))

@app.route('/checkout')
def checkout():
    cart = session.get('cart', [])
    if not session.get("user_id"):
        return redirect(url_for("login"))
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
    if not session.get("user_id"):
        return redirect(url_for("login"))
    if not cart:
        return redirect(url_for("shop_page"))

    name = request.form.get("name")
    email = request.form.get("email")
    phone = request.form.get("phone")
    address = request.form.get("address")

    # calculattion of total
    total = sum(float(item["price"]) * int(item["quantity"]) for item in cart)

    #  SAVE ORDER
    user_id = session.get("user_id")
    cursor.execute("""
        INSERT INTO orders (user_id, name, email, phone, total, status)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (user_id, name, email, phone, total, "pending"))

    order_id = cursor.lastrowid 

    for item in cart:
        cursor.execute("""
            INSERT INTO order_items (order_id, product_id,product_name,price, quantity)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            order_id,
            item["id"],
            item["name"],
            item["price"],
            item["quantity"]
        ))

    #  REDUCE STOCK
    for item in cart:
        cursor.execute("""
            UPDATE products
            SET stock = stock - %s,
                sold = sold + %s
            WHERE id = %s
        """, (
            item["quantity"],
            item["quantity"],
            item["id"]
        ))

    db.commit()

    #  CLEAR CART
    session.pop('cart', None)

    return render_template(
        'confirmation.html',
        name=name,
        email=email,
        address=address,
        phone=phone,
        cart=cart,
        total=total,
        order_id=order_id
    )


# -------------------- ERRORS --------------------

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404





# -------------------- RUN --------------------

if __name__ == "__main__":
    app.run(debug=True) 