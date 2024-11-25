from pymongo import MongoClient
from bson import ObjectId
import os
# Connect to the database

mongouser = os.environ["MONGOUSER"]
cluster = os.environ["MONGOCLUSTER"]
mongopass = os.environ["MONGOPASS"]
url = f"mongodb+srv://{mongouser}:{mongopass}@{cluster}/"
print(url)
# Database setup
client = MongoClient(url)
db = client['ecom']  # Use your database name
products_collection = db['products']
users_collection = db['users']
orders_collection = db['orders']

# --------------------- Product Functions ---------------------


def add_products(product):
    """Add a new product to the products collection."""
    try:
        products_collection.insert_one(product)
        print(f"Successfully added the product in {products_collection}")
        return "success"
    except Exception as e:
        return str(e)


def fetch_products():
    """Fetch all products from the products collection."""
    try:
        return list(products_collection.find())
    except Exception as e:
        return str(e)


def delete_product(product_id):
    """Delete a product by its ObjectId."""
    try:
        result = products_collection.delete_one({"_id": ObjectId(product_id)})
        return result.deleted_count > 0  # Return True if deletion was successful
    except Exception as e:
        return str(e)


def get_product_by_id(product_id):
    """Fetch a product by its ID."""
    try:
        product = products_collection.find_one({"_id": ObjectId(product_id)})
        if product:
            product['rating'] = product.get(
                'rating', None)  # Set rating to None if it doesn't exist
        return product
    except Exception as e:
        return None  # Return None in case of error


def search_products(query):
    """Search for products based on name or description."""
    try:
        return list(
            products_collection.find({
                '$or': [
                    {
                        'name': {
                            '$regex': query,
                            '$options': 'i'
                        }
                    },  # Case-insensitive search by name
                    {
                        'description': {
                            '$regex': query,
                            '$options': 'i'
                        }
                    }  # Case-insensitive search by description
                ]
            }))
    except Exception as e:
        return str(e)


# --------------------- User Functions ---------------------


def create_user(username, email, mobile, password):
    """Create a new user and insert it into the users collection."""
    try:
        user = {
            "username": username,
            "email": email,
            "mobile": mobile,
            "password": password  # Store hashed password for security
        }
        users_collection.insert_one(user)
        return "User created successfully"
    except Exception as e:
        return str(e)


def get_user_by_username(username):
    """Retrieve user information by username."""
    try:
        return users_collection.find_one({"username": username})
    except Exception as e:
        return None  # Return None if user not found


def get_user_by_email(email):
    """Retrieve user information by email."""
    try:
        return users_collection.find_one({"email": email})
    except Exception as e:
        return None  # Return None if email not found


# --------------------- Order Functions ---------------------


def insert_order(order):
    """Insert a new order into the orders collection."""
    try:
        orders_collection.insert_one(order)
        return "Order placed successfully"
    except Exception as e:
        return str(e)


def get_all_orders():
    """Fetch all orders from the orders collection."""
    try:
        return list(orders_collection.find())
    except Exception as e:
        return []  # Return empty list in case of error


def get_orders_by_username(username=None):
    """
    Fetch orders by username. If no username is provided, fetch all orders.
    """
    try:
        if username:
            # Case-insensitive search for orders by username
            orders = orders_collection.find(
                {"username": {
                    "$regex": username,
                    "$options": "i"
                }})
        else:
            orders = orders_collection.find()
        return list(orders)  # Convert to list for easier handling
    except Exception as e:
        print(f"Error fetching orders: {e}")
        return []  # Return an empty list if there is an error


def update_order_status(order_id, new_status, description):
    """
    Update the status of an order by order ID.
    """
    try:
        result = orders_collection.update_one({'_id': ObjectId(order_id)}, {
            '$set': {
                'status': new_status,
                'update_description': description
            }
        })
        return result.modified_count > 0  # Return True if the status was updated
    except Exception as e:
        print(f"Error updating order status: {e}")
        return False


def get_all_orders():
    """Fetch all orders."""
    try:
        return list(orders_collection.find())
    except Exception as e:
        return []  # Return empty list in case of error


admins_collection = db['admins']  # Collection to store admin users


# Function to create a new admin user
def create_admin(admin_data):
    try:
        admins_collection.insert_one(admin_data)
        return "success"
    except Exception as e:
        return str(e)


# Function to get admin by username
def get_admin_by_username(username):
    return admins_collection.find_one({'username': username})


# Function to get admin by email
def get_admin_by_email(email):
    return admins_collection.find_one({'email': email})


def count_products():
    return products_collection.count_documents({})


def count_orders():
    return orders_collection.count_documents({})


def count_users():
    return users_collection.count_documents({})


def count_orders_by_status(status):
    return orders_collection.count_documents({'status': status})


def get_monthly_order_status_counts():
    pipeline = [
        {
            '$group': {
                '_id': {
                    'year': {
                        '$year': '$date'
                    },  # Replace 'date' with your order date field
                    'month': {
                        '$month': '$date'
                    },
                    'status': '$status'
                },
                'count': {
                    '$sum': 1
                }
            }
        },
        {
            '$sort': {
                '_id.year': 1,
                '_id.month': 1
            }  # Sort by year and month
        }
    ]

    results = list(orders_collection.aggregate(pipeline))

    # Transform the results into a more usable format
    monthly_counts = {}
    for item in results:
        year_month = f"{item['_id']['year']}-{item['_id']['month']:02d}"
        if year_month not in monthly_counts:
            monthly_counts[year_month] = {}
        monthly_counts[year_month][item['_id']['status']] = item['count']

    return monthly_counts
