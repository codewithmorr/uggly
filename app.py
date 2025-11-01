from flask import Flask, render_template,request, redirect, url_for

app = Flask(__name__)


products = [
    { "id":1,
     "name": "vintage tee", 
     "price": "$34.99", "price_value":34.99,
     "image":"vintage tee.jpg",
     "description":"cotton t-shirt"},
     
      {"id":2,"name": "retro hoodie", "price": "$77.99","price_value":77.99,"image":
     "retrohoodie.jpg","description":"cotton hoodie"},
     
     
      {"id":3,
       "name": "buckethat", 
       "price": "$13.99","price_value":13.99,
       "image":"buckethat.jpg","description":"flawless bucket hat"},
    
    
     {"id":4,
      "name": "cargo pants",
        "price": "$179.99","price_value":179.99,
        "image": "cargopants.jpg","description":"green camo cargo pants"},
     
     
     {"id":5,"name": "nike back-pack[green]", "price": "$48.99","price_value": 48.99,"image":
     "nikebackpack.jpg","description":"green nylon backpack"},
     
     
     {"id":6,"name": "MJ 23 socks", "price": "$7.99","price_value":7.99,"image":
     "socks.jpg" ,"description":"high quality cotton socks"},
      

]
cart=[]

@app.route('/shop')
def shop_page():
    return render_template('shop.html', products=products)

@app.route('/')
def home():
    return render_template('syna.html')

@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/checkout')
def checkout():
    total = sum(item["price_value"] * item['quantity']for item in cart)
    return render_template('checkout.html', cart=cart, total=total)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = next((p for p  in products if p["id"] == product_id), None)
    if product is None:
        abort(404)
    return render_template('product_detail.html', product=product)

@app.route('/add_to_cart/<int:product_id>', methods=["POST"])
def add_to_cart(product_id):
    product = next((p for p in products if p["id"] == product_id), None)
    if product:
        quantity = int(request.form.get("quantity", 1))  # 👈 grab quantity from form
        size = request.form.get("size")  # optional, if you wanna store it

        # check if item already in cart
        existing_item = next((item for item in cart if item["id"] == product_id), None)
        if existing_item:
            existing_item["quantity"] += quantity
        else:
            cart.append({
                "id": product["id"],
                "name": product["name"],
                "price_value": product["price_value"],
                "price": product["price"],
                "image": product["image"],
                "description": product["description"],
                "quantity": quantity,
                "size": size
            })
    return redirect(url_for("checkout"))






@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

@app.errorhandler(500)
def internal_error(e):
    return render_template("500.html"), 500


if __name__ == "__main__":
    app.run(debug=False)
