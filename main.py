from flask import Flask, flash, redirect, render_template, request, url_for, session
from bson import ObjectId
import dbfile
from datetime import datetime
from flask_bcrypt import Bcrypt
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)
app.secret_key = '123xd'  # Change this to a strong secret key
bcrypt = Bcrypt(app)


# Initialize the shopping cart in session
@app.before_request
def initialize_cart():
    if 'cart' not in session:
        session['cart'] = []

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Assuming you have a function in dbfile to verify admin credentials
        admin = dbfile.get_admin_by_username(username)

        if admin and check_password_hash(admin['password'], password):  # Check against hashed password
            session['admin_logged_in'] = True
            flash('Logged in successfully.', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials.', 'danger')

    return render_template('admin_login.html')

# Logout Route
@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('admin_login'))



@app.route('/admin/signup', methods=['GET', 'POST'])
def admin_signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Validate the form fields
        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return redirect(url_for('admin_signup'))

        # Check if the admin username or email already exists
        existing_admin = dbfile.get_admin_by_username(username) or dbfile.get_admin_by_email(email)
        if existing_admin:
            flash('Admin with this username or email already exists.', 'danger')
            return redirect(url_for('admin_signup'))

        # Hash the password using pbkdf2:sha256 (correct method)
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        # Create new admin record
        admin_data = {
            'username': username,
            'email': email,
            'password': hashed_password  # Store hashed password
        }

        # Call the dbfile function to save the admin
        dbfile.create_admin(admin_data)
        flash('Admin registered successfully. Please log in.', 'success')
        
        # Redirect to the admin login page after successful signup
        return redirect(url_for('admin_login'))

    return render_template('admin_signup.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    # Get total counts
    total_products = dbfile.count_products()
    total_orders = dbfile.count_orders()
    total_users = dbfile.count_users()
    
    # Get order status counts
    status_counts = {
        'Processing': dbfile.count_orders_by_status('Processing'),
        'Shipped': dbfile.count_orders_by_status('Shipped'),
        'Delivered': dbfile.count_orders_by_status('Delivered'),
        'Cancelled': dbfile.count_orders_by_status('Cancelled'),
    }

    return render_template('admin_dashboard.html', 
                           total_products=total_products, 
                           total_orders=total_orders, 
                           total_users=total_users,
                           status_counts=status_counts)




@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Fetch the user by email
        user = dbfile.get_user_by_email(email)

        if user and bcrypt.check_password_hash(user['password'], password):
            # Login successful
            session['user_id'] = str(user['_id'])  # Store user ID in session
            session['username'] = user['username']  # Store username in session
            session['email'] = user['email']
            session['mobile'] = user['mobile']
            flash("Login successful!", "success")
            return redirect(url_for('index'))  # Redirect to the homepage
        else:
            flash("Invalid email or password!", "error")

    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        mobile = request.form.get('mobile')
        password = request.form.get('password')

        # Check if the username or email already exists
        existing_user = dbfile.get_user_by_username(username)
        existing_email = dbfile.get_user_by_email(email)

        if existing_user:
            flash("Username already exists!", "error")
            return redirect(url_for('signup'))

        if existing_email:
            flash("Email already registered!", "error")
            return redirect(url_for('signup'))

        # Hash the password
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        # Store user data in MongoDB
        dbfile.create_user(username, email, mobile, hashed_password)

        # Store email and mobile in session
        session['username'] = username
        session['email'] = email
        session['mobile'] = mobile

        flash("Signup successful! You can now log in.", "success")
        return redirect(url_for('login'))

    return render_template('signup.html')

@app.route('/index')
def index():
    products = dbfile.fetch_products()  # Fetch products from the database
    return render_template("base.html", products=products)

@app.route("/add_products", methods=["POST", "GET"])
def add_products():
    products = dbfile.fetch_products()  # Fetch products from the database
    if request.method == "POST":
        product_name = request.form.get("product_name")
        product_sku = request.form.get("product_sku")
        product_description = request.form.get("product_description")
        product_price = request.form.get("product_price")
        product_image = request.form.get("product_image")

        # Basic validation (ensure no fields are empty)
        if not product_name or not product_sku or not product_description or not product_price or not product_image:
            flash("All fields are required!", "error")
            return redirect(url_for('add_products'))

        # Create product dictionary
        product = {
            "name": product_name,
            "sku": product_sku,
            "description": product_description,
            "price": float(product_price),
            "image": product_image
        }
        dbfile.add_products(product)

        flash(f"Product '{product_name}' added successfully!", "success")
        return redirect(url_for('add_products'))

    return render_template("add_products.html", products=products)

@app.route('/delete_product/<product_id>', methods=['POST'])
def delete_product(product_id):
    # Call your dbfile function to delete the product by ID
    dbfile.delete_product(product_id)  # Ensure this function is defined in your dbfile

    flash("Product deleted successfully!", "success")
    return redirect(url_for('add_products'))  # Redirect to the add_products page or wherever you prefer

@app.route("/add_to_cart", methods=["POST"])
def add_to_cart():
    product_id = request.form.get("product_id")
    session['cart'].append(product_id)  # Add product ID to cart
    session.modified = True  # Mark session as modified to save changes
    flash("Product added to cart!", "success")
    return redirect(url_for('index'))

@app.route("/cart")
def view_cart():
    # Retrieve products from cart
    cart_items = [dbfile.get_product_by_id(ObjectId(product_id)) for product_id in session['cart']]
    return render_template("cart.html", cart_items=cart_items)

@app.route("/checkout", methods=["POST"])
def checkout():
    if 'cart' not in session or not session['cart']:
        flash("Your cart is empty. Please add products before checking out.", "error")
        return redirect(url_for('index'))

    # Retrieve cart items
    cart_items = [dbfile.get_product_by_id(product_id) for product_id in session['cart']]
    
    # Get address, pincode, and email from the form and session
    address = request.form.get('address')
    pincode = request.form.get('pincode')
    username = session.get('username')  # Get the username from the session
    email = session.get('email')        # Get the email from the session

    # Create an order dictionary
    order = {
        "items": cart_items,
        "total_price": sum(item['price'] for item in cart_items),
        "order_date": datetime.now(),  # Capture the current date and time
        "address": address,             # Store the address
        "pincode": pincode,             # Store the pincode
        "username": username,           # Store the username from session
        "email": email,              # Store the email from session
        "status":"ordered"
    }

    # Insert order into MongoDB
    dbfile.insert_order(order)  # Ensure this function is defined in your dbfile

    # Clear the cart
    session.pop('cart', None)
    flash("Thank you for your purchase!", "success")
    return redirect(url_for('index'))

@app.route('/search', methods=['GET'])
def search_products():
    query = request.args.get('query')  # Get the search query from the URL

    if query:
        # Call your database function to search for products
        products = dbfile.search_products(query)  # Ensure this function is defined in your dbfile
    else:
        products = []  # No products if no query is provided

    return render_template('base.html', products=products)  # Render the products page with the search results

@app.route('/product/<product_id>')
def product_detail(product_id):
    product = dbfile.get_product_by_id(product_id)  # Fetch product details from the database
    return render_template('product_detail.html', product=product)  # Render product detail template

@app.route('/order_tracker')
def order_tracker():
    username = session.get('username')
    if not username:
        flash("You need to be logged in to view your orders.", "error")
        return redirect(url_for('login'))

    orders = dbfile.get_orders_by_username(username)  # Fetch orders using the database instance
    return render_template('order_tracker.html', orders=orders)

@app.route('/admin/order_tracker', methods=['GET', 'POST'])
def admin_order_tracker():
    if request.method == 'POST':
        # Handle order status update
        order_id = request.form.get('order_id')
        new_status = request.form.get('status')
        description = request.form.get('description')
        dbfile.update_order_status(order_id, new_status,description)
        flash("Order status updated successfully.", "success")
    
    # Filter orders by username if provided
    username = request.args.get('username', None)
    if username:
        orders = dbfile.get_orders_by_username(username)
    else:
        orders = dbfile.get_orders_by_username(username)
    
    return render_template('admin_order_tracker.html', orders=list(orders))



@app.route('/products')
def view_products():
    products = dbfile.get_all_products()  # Fetch all products from the database
    return render_template('product_list.html', products=products)

@app.route('/logout')
def logout():
    # Clear the session or perform logout logic
    session.pop('username', None)  # Remove user from session
    return redirect(url_for('index'))  # Redirect to the home page or login page

if __name__ == "__main__":
    app.run(debug=True)
