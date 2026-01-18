"""
Database Management System
Student:Malak Milhem, ID: 1220031
        Layal Hajji, ID: 1220871

"""

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
import mysql.connector
from mysql.connector import Error
from datetime import datetime
import os
import re
from functools import wraps

app = Flask(__name__)
app.secret_key = 'amin_furniture_secret_key_2025'

# ==================== VALIDATION HELPERS ====================

def validate_name(name, field_name="Name"):
    """Validate that name contains only letters and spaces"""
    if not name or not name.strip():
        return False, f'{field_name} is required!'
    if not re.match(r'^[a-zA-Z\s]+$', name.strip()):
        return False, f'{field_name} must contain only letters and spaces!'
    return True, None

def validate_phone(phone):
    """Validate that phone contains only numbers"""
    if not phone or not phone.strip():
        return True, None  # Phone is optional
    if not re.match(r'^\d+$', phone.strip()):
        return False, 'Phone number must contain only numbers!'
    return True, None

def validate_date(date_str, field_name="Date", allow_future=False):
    """Validate date format (YYYY-MM-DD) and that it's a real date"""
    if not date_str or not date_str.strip():
        return True, None  # Date is optional in some cases
    
    try:
        # Check format YYYY-MM-DD
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', date_str.strip()):
            return False, f'{field_name} must be in format YYYY-MM-DD!'
        
        # Parse the date
        date_obj = datetime.strptime(date_str.strip(), '%Y-%m-%d').date()
        
        # Check month is 01-12
        if date_obj.month < 1 or date_obj.month > 12:
            return False, f'{field_name} month must be between 01 and 12!'
        
        # Check date is not in the future (only for hire_date, not for order_date)
        if not allow_future and date_obj > datetime.now().date():
            return False, f'{field_name} cannot be in the future!'
        
        # Check date is not in the past (for delivery/scheduled dates that must be in future)
        if allow_future and date_obj < datetime.now().date():
            return False, f'{field_name} cannot be in the past! Must be today or a future date.'
        
        return True, None
    except ValueError:
        return False, f'{field_name} is not a valid date!'

def validate_position(position):
    """Validate that position contains only letters and spaces"""
    if not position or not position.strip():
        return False, 'Position is required!'
    if not re.match(r'^[a-zA-Z\s]+$', position.strip()):
        return False, 'Position must contain only letters and spaces!'
    return True, None

def validate_salary(salary_str):
    """Validate that salary is a positive number"""
    if not salary_str or not salary_str.strip():
        return True, None  # Salary is optional
    try:
        salary = float(salary_str.strip())
        if salary < 0:
            return False, 'Salary must be a positive number!'
        return True, None
    except ValueError:
        return False, 'Salary must be a valid number!'

def parse_purchase_items(form):
    """Parse and validate purchase items from a submitted form"""
    product_ids = form.getlist('product_id')
    quantities = form.getlist('quantity')
    max_len = max(len(product_ids), len(quantities))
    items = []
    seen_products = set()
    
    for idx in range(max_len):
        product_id_raw = product_ids[idx].strip() if idx < len(product_ids) else ''
        quantity_raw = quantities[idx].strip() if idx < len(quantities) else ''
        
        if not product_id_raw and not quantity_raw:
            continue
        
        if not product_id_raw or not quantity_raw:
            return None, 'Each purchase item must include product and quantity.'
        
        try:
            product_id = int(product_id_raw)
            quantity = int(quantity_raw)
        except ValueError:
            return None, 'Purchase items must use valid numbers.'
        
        if product_id in seen_products:
            return None, 'Duplicate product in purchase items is not allowed.'
        if quantity <= 0:
            return None, 'Quantity must be at least 1.'
        
        items.append({
            'product_id': product_id,
            'quantity': quantity
        })
        seen_products.add(product_id)
    
    if not items:
        return None, 'Add at least one purchase item.'
    
    return items, None

# Role-based access control decorators
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please login to access this page.', 'error')
                return redirect(url_for('login'))
            if session.get('role') not in roles:
                flash('You do not have permission to access this page.', 'error')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Product images mapping by product type keywords
PRODUCT_TYPE_IMAGES = {
    # Beds
    'bed': 'https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?w=400&h=300&fit=crop',
    'king size bed': 'https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?w=400&h=300&fit=crop',
    'queen size bed': 'https://images.unsplash.com/photo-1588046130717-0eb0c9a3ba15?w=400&h=300&fit=crop',
    'single bed': 'https://images.unsplash.com/photo-1540518614846-7eded433c457?w=400&h=300&fit=crop',
    
    # Bedroom furniture
    'wardrobe': 'https://images.unsplash.com/photo-1558997519-83ea9252edf8?w=400&h=300&fit=crop',
    'nightstand': 'https://images.unsplash.com/photo-1532372320572-cda25653a26d?w=400&h=300&fit=crop',
    
    # Sofas & Living Room
    'sofa': 'https://images.unsplash.com/photo-1555041469-a586c61ea9bc?w=400&h=300&fit=crop',
    'leather sofa': 'https://images.unsplash.com/photo-1493663284031-b7e3aefcae8e?w=400&h=300&fit=crop',
    'coffee table': 'https://images.unsplash.com/photo-1533090481720-856c6e3c1fdc?w=400&h=300&fit=crop',
    'tv stand': 'https://images.pexels.com/photos/1571453/pexels-photo-1571453.jpeg?w=400&h=300&fit=crop',
    'tv': 'https://images.pexels.com/photos/1571453/pexels-photo-1571453.jpeg?w=400&h=300&fit=crop',
    'entertainment': 'https://images.pexels.com/photos/1571453/pexels-photo-1571453.jpeg?w=400&h=300&fit=crop',
    
    # Office
    'office desk': 'https://images.unsplash.com/photo-1518455027359-f3f8164ba6bd?w=400&h=300&fit=crop',
    'desk': 'https://images.unsplash.com/photo-1518455027359-f3f8164ba6bd?w=400&h=300&fit=crop',
    'office chair': 'https://images.unsplash.com/photo-1580480055273-228ff5388ef8?w=400&h=300&fit=crop',
    'ergonomic': 'https://images.unsplash.com/photo-1580480055273-228ff5388ef8?w=400&h=300&fit=crop',
    'drawers': 'https://images.pexels.com/photos/3756959/pexels-photo-3756959.jpeg?w=400&h=300&fit=crop',
    
    # Dining
    'dining table': 'https://images.unsplash.com/photo-1617806118233-18e1de247200?w=400&h=300&fit=crop',
    'dining chair': 'https://images.unsplash.com/photo-1549497538-303791108f95?w=400&h=300&fit=crop',
    'dining set': 'https://images.unsplash.com/photo-1549497538-303791108f95?w=400&h=300&fit=crop',
    
    # Kitchen
    'kitchen island': 'https://images.pexels.com/photos/1080721/pexels-photo-1080721.jpeg?w=400&h=300&fit=crop',
    'kitchen cabinet': 'https://images.pexels.com/photos/1571460/pexels-photo-1571460.jpeg?w=400&h=300&fit=crop',
    'kitchen cabinet set': 'https://images.pexels.com/photos/1571460/pexels-photo-1571460.jpeg?w=400&h=300&fit=crop',
    'cabinet set': 'https://images.pexels.com/photos/1571460/pexels-photo-1571460.jpeg?w=400&h=300&fit=crop',
}

# Fallback images by category
CATEGORY_IMAGES = {
    'Bedroom': 'https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?w=400&h=300&fit=crop',
    'Living Room': 'https://images.unsplash.com/photo-1555041469-a586c61ea9bc?w=400&h=300&fit=crop',
    'Office': 'https://images.unsplash.com/photo-1518455027359-f3f8164ba6bd?w=400&h=300&fit=crop',
    'Dining Room': 'https://images.unsplash.com/photo-1617806118233-18e1de247200?w=400&h=300&fit=crop',
    'Kitchen': 'https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=400&h=300&fit=crop',
    'default': 'https://images.unsplash.com/photo-1555041469-a586c61ea9bc?w=400&h=300&fit=crop',
}

@app.context_processor
def utility_processor():
    def get_product_image(category, product_id, product_name=''):
        """Get a product image based on product name keywords, then category"""
        product_name_lower = product_name.lower() if product_name else ''
        
        # Exact product name mappings using provided image URLs
        # Note: For Unsplash photos, using the photo ID in image format
        # For iStock photos, using the direct media URL provided
        exact_mappings = {
            # TV Stand - using working TV stand image
            'tv stand': 'https://images.unsplash.com/photo-1617486492310-ef1a3d5e3a64?w=400&h=300&fit=crop&auto=format&q=80',
            
            # Leather Sofa 3 Seater - using working sofa image
            'leather sofa 3 seater': 'https://images.unsplash.com/photo-1555041469-a586c61ea9bc?w=400&h=300&fit=crop&auto=format&q=80',
            'leather sofa': 'https://images.unsplash.com/photo-1555041469-a586c61ea9bc?w=400&h=300&fit=crop&auto=format&q=80',
            
            # Kitchen Cabinet Set - using working kitchen cabinets image
            'kitchen cabinet set': 'https://images.unsplash.com/photo-1556912172-45b7abe8b7e1?w=400&h=300&fit=crop&auto=format&q=80',
            
            # Kitchen Island - using working kitchen island image
            'kitchen island': 'https://images.unsplash.com/photo-1556912172-45b7abe8b7e1?w=400&h=300&fit=crop&auto=format&q=80',
            
            # Filing Cabinet 4 Drawers - using working filing cabinet image
            'filing cabinet 4 drawers': 'https://images.unsplash.com/photo-1535953291981-b7b55c3c5fe4?w=400&h=300&fit=crop&auto=format&q=80',
            
            # Dining Chairs Set (6) - using working dining chairs image
            'dining chairs set (6)': 'https://images.unsplash.com/photo-1617806118233-18e1de247200?w=400&h=300&fit=crop&auto=format&q=80',
            'dining chairs set': 'https://images.unsplash.com/photo-1617806118233-18e1de247200?w=400&h=300&fit=crop&auto=format&q=80',
            
            # Dining Table 6 Seater - using working dining table image
            'dining table 6 seater': 'https://images.unsplash.com/photo-1617806118233-18e1de247200?w=400&h=300&fit=crop&auto=format&q=80',
        }
        
        # Check exact matches first
        for exact_name, image_url in exact_mappings.items():
            if exact_name in product_name_lower:
                return image_url
        
        # Then try keyword matching
        for keyword, image_url in PRODUCT_TYPE_IMAGES.items():
            if keyword in product_name_lower:
                return image_url
        
        # Fallback to category image
        return CATEGORY_IMAGES.get(category, CATEGORY_IMAGES['default'])
    
    return dict(get_product_image=get_product_image)

DB_CONFIG = {
    'host': 'localhost',
    'database': 'amin_furniture',
    'user': 'root',
    'password': '1234'
}

def get_db_connection():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

# ==================== AUTHENTICATION ====================

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login page"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user_type = request.form.get('user_type')  # 'customer', 'employee', 'manager'
        
        conn = get_db_connection()
        if not conn:
            flash('Database connection failed!', 'error')
            return render_template('login.html')
        
        cursor = conn.cursor(dictionary=True)
        
        try:
            if user_type == 'customer':
                # Check customer login
                cursor.execute("""
                    SELECT CustomerID, FirstName, LastName, Email
                    FROM Customers
                    WHERE Email = %s
                """, (email,))
                user = cursor.fetchone()
                
                if user:
                    # For demo: accept any password if email exists
                    # In production, use password hashing
                    session['user_id'] = user['CustomerID']
                    session['user_name'] = f"{user['FirstName']} {user['LastName']}"
                    session['role'] = 'customer'
                    session['user_type'] = 'customer'
                    flash(f'Welcome back, {user["FirstName"]}!', 'success')
                    return redirect(url_for('customer_dashboard'))
            
            elif user_type in ['employee', 'manager', 'delivery_staff']:
                # Check employee login
                if user_type == 'manager':
                    position_filter = "Manager"
                elif user_type == 'delivery_staff':
                    position_filter = "Delivery Staff"
                else:
                    position_filter = "Sales Associate"
                    
                cursor.execute("""
                    SELECT EmployeeID, FirstName, LastName, Email, Position
                    FROM Employees
                    WHERE Email = %s AND Position = %s
                """, (email, position_filter))
                user = cursor.fetchone()
                
                if user:
                    session['user_id'] = user['EmployeeID']
                    session['user_name'] = f"{user['FirstName']} {user['LastName']}"
                    if user['Position'] == 'Manager':
                        session['role'] = 'manager'
                    elif user['Position'] == 'Delivery Staff':
                        session['role'] = 'delivery_staff'
                    else:
                        session['role'] = 'employee'
                    session['user_type'] = user['Position'].lower().replace(' ', '_')
                    flash(f'Welcome back, {user["FirstName"]}!', 'success')
                    
                    # Redirect based on role
                    if session['role'] == 'delivery_staff':
                        return redirect(url_for('delivery_dashboard'))
                    else:
                        return redirect(url_for('employee_dashboard'))
            
            flash('Invalid email or password. Please try again.', 'error')
            
        except Error as e:
            flash(f'Login error: {e}', 'error')
        finally:
            cursor.close()
            conn.close()
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """User logout"""
    session.clear()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Customer registration"""
    if request.method == 'POST':
        conn = get_db_connection()
        if not conn:
            flash('Database connection failed!', 'error')
            return redirect(url_for('register'))
        
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO Customers (FirstName, LastName, Email, PhoneNumber, Address, RegistrationDate)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                request.form['first_name'],
                request.form['last_name'],
                request.form['email'],
                request.form.get('phone_number'),
                request.form.get('address'),
                datetime.now().date()
            ))
            conn.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except Error as e:
            flash(f'Registration error: {e}', 'error')
            conn.rollback()
        finally:
            cursor.close()
            conn.close()
    
    return render_template('register.html')

# ==================== DASHBOARDS ====================

@app.route('/')
def index():
    """Redirect to appropriate dashboard based on role"""
    if 'user_id' in session:
        if session.get('role') == 'customer':
            return redirect(url_for('customer_dashboard'))
        elif session.get('role') in ['employee', 'manager']:
            return redirect(url_for('employee_dashboard'))
    return redirect(url_for('login'))

@app.route('/customer/dashboard')
@login_required
@role_required('customer')
def customer_dashboard():
    """Customer dashboard - shows their orders"""
    conn = get_db_connection()
    if not conn:
        flash('Database connection failed!', 'error')
        return render_template('customer/dashboard.html', orders=[])
    
    cursor = conn.cursor(dictionary=True)
    customer_id = session['user_id']
    
    try:
        cursor.execute("""
            SELECT o.OrderID, o.OrderDate, o.Status,
                   SUM(op.Quantity * op.PricePerUnit) as TotalAmount
            FROM Orders o
            LEFT JOIN Order_Product op ON o.OrderID = op.OrderID
            WHERE o.CustomerID = %s
            GROUP BY o.OrderID, o.OrderDate, o.Status
            ORDER BY o.OrderDate DESC
            LIMIT 10
        """, (customer_id,))
        orders = cursor.fetchall()
        for order in orders:
            if order.get('TotalAmount') is None:
                order['TotalAmount'] = 0
        
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT o.OrderID) as total_orders,
                (
                    SELECT SUM(op2.Quantity * op2.PricePerUnit)
                    FROM Orders o2
                    LEFT JOIN Order_Product op2 ON o2.OrderID = op2.OrderID
                    WHERE o2.CustomerID = %s AND o2.Status = 'Completed'
                ) as total_spent
            FROM Orders o
            WHERE o.CustomerID = %s
        """, (customer_id, customer_id))
        stats = cursor.fetchone()
        if stats and stats.get('total_spent') is None:
            stats['total_spent'] = 0
        
    except Error as e:
        flash(f'Error fetching data: {e}', 'error')
        orders = []
        stats = {'total_orders': 0, 'total_spent': 0}
    finally:
        cursor.close()
        conn.close()
    
    return render_template('customer/dashboard.html', orders=orders, stats=stats)

@app.route('/customer/catalog')
@login_required
@role_required('customer')
def customer_catalog():
    """Customer product catalog"""
    conn = get_db_connection()
    if not conn:
        flash('Database connection failed!', 'error')
        return render_template('customer/catalog.html', products=[])
    
    cursor = conn.cursor(dictionary=True)
    search = request.args.get('search', '')
    category = request.args.get('category', '')
    
    try:
        query = """
            SELECT p.ProductID, p.ProductName, p.Dimensions, p.Color, p.Material,
                   p.SellingPrice, p.StockQuantity, p.DateAdded,
                   p.CategoryName, s.SupplierName
            FROM Products p
            LEFT JOIN Suppliers s ON p.SupplierID = s.SupplierID
            WHERE p.StockQuantity > 0
        """
        params = []
        
        if search:
            query += " AND (p.ProductName LIKE %s OR p.Material LIKE %s)"
            params.extend([f'%{search}%', f'%{search}%'])
        
        if category:
            query += " AND p.CategoryName = %s"
            params.append(category)
        
        query += " ORDER BY p.ProductName"
        
        cursor.execute(query, params)
        products = cursor.fetchall()
        
        cursor.execute("""
            SELECT DISTINCT CategoryName
            FROM Products
            WHERE CategoryName IS NOT NULL AND CategoryName <> ''
            ORDER BY CategoryName
        """)
        categories = cursor.fetchall()
        
    except Error as e:
        flash(f'Error fetching products: {e}', 'error')
        products = []
        categories = []
    finally:
        cursor.close()
        conn.close()
    
    return render_template('customer/catalog.html', products=products, categories=categories, 
                         search=search, selected_category=category)

@app.route('/customer/cart')
@login_required
@role_required('customer')
def customer_cart():
    """Shopping cart page"""
    cart = session.get('cart', {})
    conn = get_db_connection()
    if not conn:
        return render_template('customer/cart.html', cart_items=[], total=0)
    
    cursor = conn.cursor(dictionary=True)
    cart_items = []
    total = 0
    
    try:
        for product_id, quantity in cart.items():
            cursor.execute("""
                SELECT ProductID, ProductName, SellingPrice, StockQuantity, Color, Material
                FROM Products
                WHERE ProductID = %s
            """, (product_id,))
            product = cursor.fetchone()
            if product:
                product['quantity'] = quantity
                product['subtotal'] = product['SellingPrice'] * quantity
                total += product['subtotal']
                cart_items.append(product)
    except Error as e:
        flash(f'Error loading cart: {e}', 'error')
    finally:
        cursor.close()
        conn.close()
    
    return render_template('customer/cart.html', cart_items=cart_items, total=total)

@app.route('/customer/cart/add/<int:product_id>', methods=['POST'])
@login_required
@role_required('customer')
def add_to_cart(product_id):
    """Add product to cart"""
    quantity = int(request.form.get('quantity', 1))
    
    if 'cart' not in session:
        session['cart'] = {}
    
    if str(product_id) in session['cart']:
        session['cart'][str(product_id)] += quantity
    else:
        session['cart'][str(product_id)] = quantity
    
    session.modified = True
    flash('Product added to cart!', 'success')
    return redirect(url_for('customer_catalog'))

@app.route('/customer/cart/remove/<int:product_id>', methods=['POST'])
@login_required
@role_required('customer')
def remove_from_cart(product_id):
    """Remove product from cart"""
    if 'cart' in session and str(product_id) in session['cart']:
        del session['cart'][str(product_id)]
        session.modified = True
        flash('Product removed from cart.', 'success')
    return redirect(url_for('customer_cart'))

@app.route('/customer/checkout', methods=['GET', 'POST'])
@login_required
@role_required('customer')
def customer_checkout():
    """Checkout and place order"""
    if request.method == 'POST':
        cart = session.get('cart', {})
        if not cart:
            flash('Your cart is empty!', 'error')
            return redirect(url_for('customer_cart'))
        
        conn = get_db_connection()
        if not conn:
            flash('Database connection failed!', 'error')
            return redirect(url_for('customer_cart'))
        
        cursor = conn.cursor(dictionary=True)
        customer_id = session['user_id']
        
        try:
            # Calculate total
            total_amount = 0
            order_items = []
            
            for product_id, quantity in cart.items():
                cursor.execute("SELECT SellingPrice, StockQuantity FROM Products WHERE ProductID = %s", (product_id,))
                product = cursor.fetchone()
                if product and product['StockQuantity'] >= quantity:
                    price = product['SellingPrice']
                    total_amount += price * quantity
                    order_items.append({
                        'product_id': product_id,
                        'quantity': quantity,
                        'price': price
                    })
                else:
                    flash(f'Insufficient stock for product ID {product_id}', 'error')
                    return redirect(url_for('customer_cart'))
            
            # Get delivery address and payment information
            delivery_address = request.form.get('delivery_address', '')
            payment_method = request.form.get('payment_method', '')
            
            if not payment_method:
                flash('Please select a payment method!', 'error')
                return redirect(url_for('customer_checkout'))
            
            # Validate payment information based on method
            if payment_method == 'Card':
                card_number = request.form.get('card_number', '').replace(' ', '')
                card_expiry = request.form.get('card_expiry', '')
                card_cvv = request.form.get('card_cvv', '')
                card_name = request.form.get('card_name', '')
                
                # Validate card number (16 digits)
                if not card_number or len(card_number) != 16 or not card_number.isdigit():
                    flash('Card number must be exactly 16 digits!', 'error')
                    return redirect(url_for('customer_checkout'))
                
                # Validate expiry date
                if not card_expiry or '/' not in card_expiry:
                    flash('Please enter a valid expiry date (MM/YY)!', 'error')
                    return redirect(url_for('customer_checkout'))
                
                try:
                    month_str, year_str = card_expiry.split('/')
                    month = int(month_str)
                    year = int('20' + year_str)  # Convert YY to YYYY
                    
                    # Validate month (01-12)
                    if month < 1 or month > 12:
                        flash('Expiry month must be between 01 and 12!', 'error')
                        return redirect(url_for('customer_checkout'))
                    
                    # Check if date is not in the past
                    expiry_date = datetime(year, month, 1)
                    today = datetime.now()
                    if expiry_date < today.replace(day=1):
                        flash('Card expiry date cannot be in the past!', 'error')
                        return redirect(url_for('customer_checkout'))
                    
                    # Check if date is not more than 5 years in future
                    max_future_date = today.replace(year=today.year + 5)
                    if expiry_date > max_future_date:
                        flash('Card expiry date must be within 5 years in the future!', 'error')
                        return redirect(url_for('customer_checkout'))
                        
                except (ValueError, IndexError):
                    flash('Invalid expiry date format! Please use MM/YY format.', 'error')
                    return redirect(url_for('customer_checkout'))
                
                # Validate CVV (3 digits)
                if not card_cvv or len(card_cvv) != 3 or not card_cvv.isdigit():
                    flash('CVV must be exactly 3 digits!', 'error')
                    return redirect(url_for('customer_checkout'))
                
                # Validate cardholder name (letters and spaces only, no numbers)
                if not card_name or not card_name.replace(' ', '').isalpha() or not card_name.strip():
                    flash('Cardholder name must contain only letters and spaces!', 'error')
                    return redirect(url_for('customer_checkout'))
                
            elif payment_method == 'Bank Transfer':
                bank_name = request.form.get('bank_name', '')
                account_number = request.form.get('account_number', '')
                transfer_ref = request.form.get('transfer_ref', '')
                
                # Validate bank name (must be text, not just numbers)
                if not bank_name or not bank_name.strip():
                    flash('Bank name is required!', 'error')
                    return redirect(url_for('customer_checkout'))
                
                # Check if bank name contains at least some letters (not all numbers)
                if bank_name.replace(' ', '').isdigit():
                    flash('Bank name must contain letters, not just numbers!', 'error')
                    return redirect(url_for('customer_checkout'))
                
                # Validate account number (must be numeric)
                if not account_number or not account_number.replace(' ', '').replace('-', '').isdigit():
                    flash('Account number must contain only numbers!', 'error')
                    return redirect(url_for('customer_checkout'))
                
            elif payment_method == 'E-payment':
                epayment_provider = request.form.get('epayment_provider', '')
                epayment_id = request.form.get('epayment_id', '')
                
                if not epayment_provider:
                    flash('Please select an e-payment provider!', 'error')
                    return redirect(url_for('customer_checkout'))
            
            # Create order
            cursor.execute("""
                INSERT INTO Orders (CustomerID, OrderDate, Status)
                VALUES (%s, %s, 'Pending')
            """, (customer_id, datetime.now().date()))
            
            order_id = cursor.lastrowid
            
            # Add order products and update stock
            for item in order_items:
                cursor.execute("""
                    INSERT INTO Order_Product (OrderID, ProductID, Quantity, PricePerUnit)
                    VALUES (%s, %s, %s, %s)
                """, (order_id, item['product_id'], item['quantity'], item['price']))
                
                cursor.execute("""
                    UPDATE Products 
                    SET StockQuantity = StockQuantity - %s 
                    WHERE ProductID = %s
                """, (item['quantity'], item['product_id']))
            
            # Create payment record
            cursor.execute("""
                INSERT INTO Payments (OrderID, PaymentDate, AmountPaid, PaymentMethod)
                VALUES (%s, %s, %s, %s)
            """, (order_id, datetime.now().date(), total_amount, payment_method))
            
            # Create delivery record if address provided
            if delivery_address:
                scheduled_date = datetime.now().date()
                cursor.execute("""
                    INSERT INTO Delivery (OrderID, DeliveryAddress, ScheduledDate)
                    VALUES (%s, %s, %s)
                """, (order_id, delivery_address, scheduled_date))
            
            conn.commit()
            session['cart'] = {}
            session.modified = True
            flash(f'Order #{order_id} placed successfully!', 'success')
            return redirect(url_for('customer_dashboard'))
            
        except Error as e:
            flash(f'Error placing order: {e}', 'error')
            conn.rollback()
        finally:
            cursor.close()
            conn.close()
    
    # GET request - show checkout page
    cart = session.get('cart', {})
    if not cart:
        return redirect(url_for('customer_cart'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cart_items = []
    total = 0
    
    try:
        for product_id, quantity in cart.items():
            cursor.execute("SELECT ProductID, ProductName, SellingPrice FROM Products WHERE ProductID = %s", (product_id,))
            product = cursor.fetchone()
            if product:
                product['quantity'] = quantity
                product['subtotal'] = product['SellingPrice'] * quantity
                total += product['subtotal']
                cart_items.append(product)
    finally:
        cursor.close()
        conn.close()
    
    return render_template('customer/checkout.html', cart_items=cart_items, total=total)

@app.route('/customer/orders/<int:order_id>')
@login_required
@role_required('customer')
def customer_order_details(order_id):
    """Customer view of their own order details"""
    conn = get_db_connection()
    if not conn:
        flash('Database connection failed!', 'error')
        return redirect(url_for('customer_dashboard'))
    
    customer_id = session['user_id']
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Verify order belongs to this customer
        cursor.execute("""
            SELECT o.*, c.FirstName, c.LastName, c.Email, c.PhoneNumber, c.Address,
                   e.FirstName as EmpFirstName, e.LastName as EmpLastName,
                   SUM(op.Quantity * op.PricePerUnit) as TotalAmount
            FROM Orders o
            JOIN Customers c ON o.CustomerID = c.CustomerID
            LEFT JOIN Employees e ON o.EmployeeID = e.EmployeeID
            LEFT JOIN Order_Product op ON o.OrderID = op.OrderID
            WHERE o.OrderID = %s AND o.CustomerID = %s
            GROUP BY o.OrderID, o.CustomerID, o.EmployeeID, o.OrderDate, o.Status,
                     c.FirstName, c.LastName, c.Email, c.PhoneNumber, c.Address,
                     e.FirstName, e.LastName
        """, (order_id, customer_id))
        order = cursor.fetchone()
        
        if not order:
            flash('Order not found or you do not have permission to view it!', 'error')
            return redirect(url_for('customer_dashboard'))
        
        # Handle NULL TotalAmount
        if order.get('TotalAmount') is None:
            order['TotalAmount'] = 0
        
        cursor.execute("""
            SELECT op.*, p.ProductName, p.Material, p.Color
            FROM Order_Product op
            JOIN Products p ON op.ProductID = p.ProductID
            WHERE op.OrderID = %s
        """, (order_id,))
        order_products = cursor.fetchall()
        
        cursor.execute("""
            SELECT * FROM Payments WHERE OrderID = %s ORDER BY PaymentDate
        """, (order_id,))
        payments = cursor.fetchall()
        
        cursor.execute("""
            SELECT d.*, e.FirstName, e.LastName
            FROM Delivery d
            LEFT JOIN Employees e ON d.EmployeeID = e.EmployeeID
            WHERE d.OrderID = %s
        """, (order_id,))
        delivery = cursor.fetchone()
        
    except Error as e:
        flash(f'Error fetching order details: {e}', 'error')
        return redirect(url_for('customer_dashboard'))
    finally:
        cursor.close()
        conn.close()
    
    return render_template('customer/order_details.html', order=order, order_products=order_products,
                         payments=payments, delivery=delivery)

@app.route('/customer/orders/<int:order_id>/cancel', methods=['POST'])
@login_required
@role_required('customer')
def customer_cancel_order(order_id):
    """Customer cancels their own order (only if Pending or Processing)"""
    conn = get_db_connection()
    if not conn:
        flash('Database connection failed!', 'error')
        return redirect(url_for('customer_dashboard'))
    
    customer_id = session['user_id']
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Verify order belongs to this customer and is cancellable
        cursor.execute("""
            SELECT OrderID, Status, CustomerID 
            FROM Orders 
            WHERE OrderID = %s AND CustomerID = %s
        """, (order_id, customer_id))
        order = cursor.fetchone()
        
        if not order:
            flash('Order not found or you do not have permission!', 'error')
            return redirect(url_for('customer_dashboard'))
        
        # Only allow cancellation for Pending or Processing orders
        if order['Status'] not in ['Pending', 'Processing']:
            if order['Status'] == 'Completed':
                flash('Cannot cancel a completed order!', 'error')
            elif order['Status'] == 'Cancelled':
                flash('Order is already cancelled!', 'error')
            else:
                flash(f'Cannot cancel order with status "{order["Status"]}". Only Pending or Processing orders can be cancelled.', 'error')
            return redirect(url_for('customer_order_details', order_id=order_id))
        
        # Update order status to Cancelled
        cursor.execute("""
            UPDATE Orders 
            SET Status = 'Cancelled' 
            WHERE OrderID = %s
        """, (order_id,))
        
        # Return products to stock
        cursor.execute("""
            SELECT op.ProductID, op.Quantity
            FROM Order_Product op
            WHERE op.OrderID = %s
        """, (order_id,))
        order_items = cursor.fetchall()
        
        for item in order_items:
            cursor.execute("""
                UPDATE Products 
                SET StockQuantity = StockQuantity + %s 
                WHERE ProductID = %s
            """, (item['Quantity'], item['ProductID']))
        
        conn.commit()
        flash(f'Order #{order_id} has been cancelled. Stock has been returned.', 'success')
        
    except Error as e:
        flash(f'Error cancelling order: {e}', 'error')
        conn.rollback()
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('customer_order_details', order_id=order_id))

@app.route('/customer/profile')
@login_required
@role_required('customer')
def customer_profile():
    """Customer profile page"""
    conn = get_db_connection()
    if not conn:
        flash('Database connection failed!', 'error')
        return redirect(url_for('customer_dashboard'))
    
    customer_id = session['user_id']
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT * FROM Customers WHERE CustomerID = %s
        """, (customer_id,))
        customer = cursor.fetchone()
        
        if not customer:
            flash('Customer not found!', 'error')
            return redirect(url_for('customer_dashboard'))
        
        # Get order statistics
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT o.OrderID) as total_orders,
                (
                    SELECT SUM(op2.Quantity * op2.PricePerUnit)
                    FROM Orders o2
                    LEFT JOIN Order_Product op2 ON o2.OrderID = op2.OrderID
                    WHERE o2.CustomerID = %s AND o2.Status = 'Completed'
                ) as total_spent,
                (
                    SELECT COUNT(DISTINCT o3.OrderID)
                    FROM Orders o3
                    WHERE o3.CustomerID = %s AND o3.Status = 'Pending'
                ) as pending_orders,
                (
                    SELECT COUNT(DISTINCT o4.OrderID)
                    FROM Orders o4
                    WHERE o4.CustomerID = %s AND o4.Status = 'Completed'
                ) as completed_orders
            FROM Orders o
            WHERE o.CustomerID = %s
        """, (customer_id, customer_id, customer_id, customer_id))
        stats = cursor.fetchone()
        
        # Get recent orders
        cursor.execute("""
            SELECT o.OrderID, o.OrderDate, o.Status,
                   SUM(op.Quantity * op.PricePerUnit) as TotalAmount
            FROM Orders o
            LEFT JOIN Order_Product op ON o.OrderID = op.OrderID
            WHERE o.CustomerID = %s
            GROUP BY o.OrderID, o.OrderDate, o.Status
            ORDER BY o.OrderDate DESC
            LIMIT 5
        """, (customer_id,))
        recent_orders = cursor.fetchall()
        
    except Error as e:
        flash(f'Error fetching profile: {e}', 'error')
        return redirect(url_for('customer_dashboard'))
    finally:
        cursor.close()
        conn.close()
    
    return render_template('customer/profile.html', customer=customer, stats=stats, recent_orders=recent_orders)

@app.route('/employee/profile')
@login_required
@role_required('employee','delivery_staff','manager')
def employee_profile():
    """Employee/Manager profile page"""
    conn = get_db_connection()
    if not conn:
        flash('Database connection failed!', 'error')
        return redirect(url_for('employee_dashboard'))
    
    employee_id = session['user_id']
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT * FROM Employees WHERE EmployeeID = %s
        """, (employee_id,))
        employee = cursor.fetchone()
        
        if not employee:
            flash('Employee not found!', 'error')
            return redirect(url_for('employee_dashboard'))
        
        if employee.get('Position') == 'Delivery Staff':
            cursor.execute("""
                SELECT 
                    COUNT(DISTINCT d.OrderID) as total_orders_handled,
                    SUM(op.Quantity * op.PricePerUnit) as total_sales,
                    (
                        SELECT COUNT(DISTINCT d2.OrderID)
                        FROM Delivery d2
                        JOIN Orders o2 ON d2.OrderID = o2.OrderID
                        WHERE d2.EmployeeID = %s AND o2.Status IN ('Ready to Deliver', 'Scheduled for Delivery')
                    ) as pending_orders,
                    (
                        SELECT COUNT(DISTINCT d3.OrderID)
                        FROM Delivery d3
                        JOIN Orders o3 ON d3.OrderID = o3.OrderID
                        WHERE d3.EmployeeID = %s AND o3.Status = 'Completed'
                    ) as completed_orders
                FROM Delivery d
                JOIN Orders o ON d.OrderID = o.OrderID
                LEFT JOIN Order_Product op ON o.OrderID = op.OrderID
                WHERE d.EmployeeID = %s
            """, (employee_id, employee_id, employee_id))
            stats = cursor.fetchone()
        else:
            cursor.execute("""
                SELECT 
                    COUNT(DISTINCT o.OrderID) as total_orders_handled,
                    SUM(op.Quantity * op.PricePerUnit) as total_sales,
                    (
                        SELECT COUNT(DISTINCT o2.OrderID)
                        FROM Orders o2
                        WHERE o2.EmployeeID = %s AND o2.Status = 'Pending'
                    ) as pending_orders,
                    (
                        SELECT COUNT(DISTINCT o3.OrderID)
                        FROM Orders o3
                        WHERE o3.EmployeeID = %s AND o3.Status = 'Completed'
                    ) as completed_orders
                FROM Orders o
                LEFT JOIN Order_Product op ON o.OrderID = op.OrderID
                WHERE o.EmployeeID = %s
            """, (employee_id, employee_id, employee_id))
            stats = cursor.fetchone()
        
        if stats and stats.get('total_sales') is None:
            stats['total_sales'] = 0
        
        cursor.execute("""
            SELECT COUNT(*) as received_purchases, SUM(TotalCost) as total_received_cost
            FROM Purchases
            WHERE ReceivedBy = %s
        """, (employee_id,))
        purchase_stats = cursor.fetchone()
        stats['received_purchases'] = purchase_stats.get('received_purchases', 0) if purchase_stats else 0
        stats['total_received_cost'] = purchase_stats.get('total_received_cost') or 0
        
        if employee.get('Position') == 'Delivery Staff':
            cursor.execute("""
                SELECT o.OrderID, o.OrderDate, o.Status,
                       SUM(op.Quantity * op.PricePerUnit) as TotalAmount,
                       c.FirstName, c.LastName
                FROM Delivery d
                JOIN Orders o ON d.OrderID = o.OrderID
                JOIN Customers c ON o.CustomerID = c.CustomerID
                LEFT JOIN Order_Product op ON o.OrderID = op.OrderID
                WHERE d.EmployeeID = %s
                GROUP BY o.OrderID, o.OrderDate, o.Status, c.FirstName, c.LastName
                ORDER BY o.OrderDate DESC
                LIMIT 5
            """, (employee_id,))
        else:
            cursor.execute("""
                SELECT o.OrderID, o.OrderDate, o.Status,
                       SUM(op.Quantity * op.PricePerUnit) as TotalAmount,
                       c.FirstName, c.LastName
                FROM Orders o
                JOIN Customers c ON o.CustomerID = c.CustomerID
                LEFT JOIN Order_Product op ON o.OrderID = op.OrderID
                WHERE o.EmployeeID = %s
                GROUP BY o.OrderID, o.OrderDate, o.Status, c.FirstName, c.LastName
                ORDER BY o.OrderDate DESC
                LIMIT 5
            """, (employee_id,))
        
        recent_orders = cursor.fetchall()
        for order in recent_orders:
            if order.get('TotalAmount') is None:
                order['TotalAmount'] = 0
        
    except Error as e:
        flash(f'Error fetching profile: {e}', 'error')
        return redirect(url_for('employee_dashboard'))
    finally:
        cursor.close()
        conn.close()
    
    is_manager = session.get('role') == 'manager'
    return render_template('employee/profile.html', employee=employee, stats=stats, 
                         recent_orders=recent_orders, is_manager=is_manager)

@app.route('/employee/dashboard')
@login_required
@role_required('employee', 'manager')
def employee_dashboard():
    """Employee/Manager dashboard"""
    conn = get_db_connection()
    if not conn:
        flash('Database connection failed!', 'error')
        return render_template('employee/dashboard.html', stats={}, is_manager=False)
    
    cursor = conn.cursor(dictionary=True)
    is_manager = session.get('role') == 'manager'
    stats = {}
    
    try:
        cursor.execute("SELECT COUNT(*) as count FROM Products")
        stats['total_products'] = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM Products WHERE StockQuantity < 10")
        stats['low_stock'] = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM Orders WHERE Status = 'Pending'")
        stats['pending_orders'] = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM Orders")
        stats['total_orders'] = cursor.fetchone()['count']
        
        cursor.execute("""
            SELECT o.OrderID, o.OrderDate, o.Status,
                   SUM(op.Quantity * op.PricePerUnit) as TotalAmount,
                   c.FirstName, c.LastName
            FROM Orders o
            JOIN Customers c ON o.CustomerID = c.CustomerID
            LEFT JOIN Order_Product op ON o.OrderID = op.OrderID
            GROUP BY o.OrderID, o.OrderDate, o.Status, c.FirstName, c.LastName
            ORDER BY o.OrderDate DESC
            LIMIT 5
        """)
        recent_orders = cursor.fetchall()
        # Handle NULL TotalAmount
        for order in recent_orders:
            if order.get('TotalAmount') is None:
                order['TotalAmount'] = 0
        stats['recent_orders'] = recent_orders
        
    except Error as e:
        flash(f'Error fetching statistics: {e}', 'error')
    finally:
        cursor.close()
        conn.close()
    
    return render_template('employee/dashboard.html', stats=stats, is_manager=is_manager)

# ==================== PROTECTED ADMIN ROUTES ====================
# All product, order, customer, supplier management routes now require employee/manager role

@app.route('/products')
@login_required
@role_required('employee', 'manager')
def products():
    """Display all products with search and filter functionality"""
    conn = get_db_connection()
    if not conn:
        flash('Database connection failed!', 'error')
        return render_template('products.html', products=[])
    
    cursor = conn.cursor(dictionary=True)
    search = request.args.get('search', '')
    category = request.args.get('category', '')
    
    try:
        query = """
            SELECT p.ProductID, p.ProductName, p.Dimensions, p.Color, p.Material,
                   p.SellingPrice, p.StockQuantity, p.DateAdded,
                   p.CategoryName, s.SupplierName
            FROM Products p
            LEFT JOIN Suppliers s ON p.SupplierID = s.SupplierID
            WHERE 1=1
        """
        params = []
        
        if search:
            query += " AND (p.ProductName LIKE %s OR p.Material LIKE %s)"
            params.extend([f'%{search}%', f'%{search}%'])
        
        if category:
            query += " AND p.CategoryName = %s"
            params.append(category)
        
        query += " ORDER BY p.ProductName"
        
        cursor.execute(query, params)
        products = cursor.fetchall()
        
        cursor.execute("""
            SELECT DISTINCT CategoryName
            FROM Products
            WHERE CategoryName IS NOT NULL AND CategoryName <> ''
            ORDER BY CategoryName
        """)
        categories = cursor.fetchall()
        
    except Error as e:
        flash(f'Error fetching products: {e}', 'error')
        products = []
        categories = []
    finally:
        cursor.close()
        conn.close()
    
    return render_template('products.html', products=products, categories=categories, 
                         search=search, selected_category=category)

@app.route('/products/add', methods=['GET', 'POST'])
@login_required
@role_required('employee', 'manager')
def add_product():
    if request.method == 'POST':
        conn = get_db_connection()
        if not conn:
            flash('Database connection failed!', 'error')
            return redirect(url_for('products'))
        
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO Products (ProductName, Dimensions, Color, Material, SellingPrice,
                                   StockQuantity, CategoryName, SupplierID, DateAdded)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                request.form['product_name'],
                request.form['dimensions'],
                request.form['color'],
                request.form['material'],
                float(request.form['selling_price']),
                int(request.form['stock_quantity']),
                request.form.get('category_name') or None,
                int(request.form['supplier_id']) if request.form['supplier_id'] else None,
                datetime.now().date()
            ))
            conn.commit()
            flash('Product added successfully!', 'success')
            return redirect(url_for('products'))
        except Error as e:
            flash(f'Error adding product: {e}', 'error')
            conn.rollback()
        finally:
            cursor.close()
            conn.close()
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    categories = []
    suppliers = []
    
    try:
        cursor.execute("""
            SELECT DISTINCT CategoryName
            FROM Products
            WHERE CategoryName IS NOT NULL AND CategoryName <> ''
            ORDER BY CategoryName
        """)
        categories = cursor.fetchall()
        cursor.execute("SELECT SupplierID, SupplierName FROM Suppliers ORDER BY SupplierName")
        suppliers = cursor.fetchall()
    except Error as e:
        flash(f'Error loading form data: {e}', 'error')
    finally:
        cursor.close()
        conn.close()
    
    return render_template('add_product.html', categories=categories, suppliers=suppliers)

@app.route('/products/<int:product_id>/update', methods=['GET', 'POST'])
@login_required
@role_required('employee', 'manager')
def update_product(product_id):
    """Update an existing product"""
    conn = get_db_connection()
    if not conn:
        flash('Database connection failed!', 'error')
        return redirect(url_for('products'))
    
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        try:
            cursor.execute("""
                UPDATE Products
                SET ProductName = %s, Dimensions = %s, Color = %s, Material = %s,
                    SellingPrice = %s, StockQuantity = %s, CategoryName = %s, SupplierID = %s
                WHERE ProductID = %s
            """, (
                request.form['product_name'],
                request.form['dimensions'],
                request.form['color'],
                request.form['material'],
                float(request.form['selling_price']),
                int(request.form['stock_quantity']),
                request.form.get('category_name') or None,
                int(request.form['supplier_id']) if request.form['supplier_id'] else None,
                product_id
            ))
            conn.commit()
            flash('Product updated successfully!', 'success')
            return redirect(url_for('products'))
        except Error as e:
            flash(f'Error updating product: {e}', 'error')
            conn.rollback()
        finally:
            cursor.close()
            conn.close()
            return redirect(url_for('products'))
    
    try:
        cursor.execute("""
            SELECT * FROM Products WHERE ProductID = %s
        """, (product_id,))
        product = cursor.fetchone()
        
        if not product:
            flash('Product not found!', 'error')
            return redirect(url_for('products'))
        
        cursor.execute("""
            SELECT DISTINCT CategoryName
            FROM Products
            WHERE CategoryName IS NOT NULL AND CategoryName <> ''
            ORDER BY CategoryName
        """)
        categories = cursor.fetchall()
        cursor.execute("SELECT SupplierID, SupplierName FROM Suppliers ORDER BY SupplierName")
        suppliers = cursor.fetchall()
        
    except Error as e:
        flash(f'Error loading product: {e}', 'error')
        return redirect(url_for('products'))
    finally:
        cursor.close()
        conn.close()
    
    return render_template('update_product.html', product=product, 
                         categories=categories, suppliers=suppliers)

@app.route('/products/<int:product_id>/delete', methods=['POST'])
@login_required
@role_required('manager')
def delete_product(product_id):
    """Delete a product (Manager only)"""
    conn = get_db_connection()
    if not conn:
        flash('Database connection failed!', 'error')
        return redirect(url_for('products'))
    
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Check if product exists
        cursor.execute("SELECT ProductName FROM Products WHERE ProductID = %s", (product_id,))
        product = cursor.fetchone()
        
        if not product:
            flash('Product not found!', 'error')
            return redirect(url_for('products'))
        
        # Check if product is in any orders
        cursor.execute("SELECT COUNT(*) as count FROM Order_Product WHERE ProductID = %s", (product_id,))
        order_count = cursor.fetchone()['count']
        
        if order_count > 0:
            flash(f'Cannot delete product "{product["ProductName"]}" because it is used in {order_count} order(s)!', 'error')
            return redirect(url_for('products'))
        
        # Delete the product
        cursor.execute("DELETE FROM Products WHERE ProductID = %s", (product_id,))
        conn.commit()
        flash(f'Product "{product["ProductName"]}" deleted successfully!', 'success')
        
    except Error as e:
        flash(f'Error deleting product: {e}', 'error')
        conn.rollback()
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('products'))

@app.route('/orders')
@login_required
@role_required('employee', 'manager')
def orders():
    conn = get_db_connection()
    if not conn:
        flash('Database connection failed!', 'error')
        return render_template('orders.html', orders=[])
    
    cursor = conn.cursor(dictionary=True)
    status_filter = request.args.get('status', '')
    search = request.args.get('search', '')
    
    try:
        query = """
            SELECT o.OrderID, o.OrderDate, o.Status,
                   SUM(op.Quantity * op.PricePerUnit) as TotalAmount,
                   c.FirstName, c.LastName, c.PhoneNumber, c.Email,
                   e.FirstName as EmpFirstName, e.LastName as EmpLastName
            FROM Orders o
            JOIN Customers c ON o.CustomerID = c.CustomerID
            LEFT JOIN Employees e ON o.EmployeeID = e.EmployeeID
            LEFT JOIN Order_Product op ON o.OrderID = op.OrderID
            WHERE 1=1
            GROUP BY o.OrderID, o.OrderDate, o.Status, c.FirstName, c.LastName, c.PhoneNumber, c.Email, e.FirstName, e.LastName
        """
        params = []
        
        if status_filter:
            query += " AND o.Status = %s"
            params.append(status_filter)
        
        if search:
            query += " AND (c.FirstName LIKE %s OR c.LastName LIKE %s OR c.Email LIKE %s OR c.PhoneNumber LIKE %s OR o.OrderID LIKE %s)"
            search_pattern = f'%{search}%'
            params.extend([search_pattern, search_pattern, search_pattern, search_pattern, search_pattern])
        
        query += " ORDER BY o.OrderDate DESC"
        
        cursor.execute(query, params)
        orders = cursor.fetchall()
        # Handle NULL TotalAmount
        for order in orders:
            if order.get('TotalAmount') is None:
                order['TotalAmount'] = 0
        
    except Error as e:
        flash(f'Error fetching orders: {e}', 'error')
        orders = []
    finally:
        cursor.close()
        conn.close()
    
    return render_template('orders.html', orders=orders, status_filter=status_filter, search=search)

@app.route('/orders/<int:order_id>')
def order_details(order_id):
    """View detailed information about a specific order"""
    conn = get_db_connection()
    if not conn:
        flash('Database connection failed!', 'error')
        return redirect(url_for('orders'))
    
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT o.*, c.FirstName, c.LastName, c.Email, c.PhoneNumber, c.Address,
                   e.FirstName as EmpFirstName, e.LastName as EmpLastName,
                   SUM(op.Quantity * op.PricePerUnit) as TotalAmount
            FROM Orders o
            JOIN Customers c ON o.CustomerID = c.CustomerID
            LEFT JOIN Employees e ON o.EmployeeID = e.EmployeeID
            LEFT JOIN Order_Product op ON o.OrderID = op.OrderID
            WHERE o.OrderID = %s
            GROUP BY o.OrderID, c.FirstName, c.LastName, c.Email, c.PhoneNumber, c.Address,
                     e.FirstName, e.LastName, o.CustomerID, o.EmployeeID, o.OrderDate, o.Status
        """, (order_id,))
        order = cursor.fetchone()
        
        if not order:
            flash('Order not found!', 'error')
            return redirect(url_for('orders'))
        
        # Handle NULL TotalAmount
        if order.get('TotalAmount') is None:
            order['TotalAmount'] = 0
        
        cursor.execute("""
            SELECT op.*, p.ProductName, p.Material, p.Color
            FROM Order_Product op
            JOIN Products p ON op.ProductID = p.ProductID
            WHERE op.OrderID = %s
        """, (order_id,))
        order_products = cursor.fetchall()
        
        cursor.execute("""
            SELECT * FROM Payments WHERE OrderID = %s ORDER BY PaymentDate
        """, (order_id,))
        payments = cursor.fetchall()
        
        cursor.execute("""
            SELECT d.*, e.FirstName, e.LastName
            FROM Delivery d
            LEFT JOIN Employees e ON d.EmployeeID = e.EmployeeID
            WHERE d.OrderID = %s
        """, (order_id,))
        delivery = cursor.fetchone()
        
    except Error as e:
        flash(f'Error fetching order details: {e}', 'error')
        return redirect(url_for('orders'))
    finally:
        cursor.close()
        conn.close()
    
    return render_template('order_details.html', order=order, order_products=order_products,
                         payments=payments, delivery=delivery)

@app.route('/orders/<int:order_id>/update_status', methods=['POST'])
@login_required
@role_required('employee', 'manager')
def update_order_status(order_id):
    """Update order status and assign employee if not already assigned"""
    conn = get_db_connection()
    if not conn:
        flash('Database connection failed!', 'error')
        return redirect(url_for('orders'))
    
    cursor = conn.cursor(dictionary=True)
    new_status = request.form.get('status')
    employee_id = session.get('user_id')  # Current logged-in employee
    
    try:
        # Check current order status and employee assignment
        cursor.execute("SELECT EmployeeID, Status FROM Orders WHERE OrderID = %s", (order_id,))
        current_order = cursor.fetchone()
        
        if not current_order:
            flash('Order not found!', 'error')
            return redirect(url_for('orders'))
        
        # Validate status transitions for employees/managers
        valid_statuses = ['Pending', 'Processing', 'Ready to Deliver', 'Scheduled for Delivery', 'Completed']
        if new_status not in valid_statuses:
            flash('Invalid status!', 'error')
            return redirect(url_for('order_details', order_id=order_id))
        
        # If changing from Pending, employee must assign themselves
        # Employees can change from Pending to Processing or Ready to Deliver
        if current_order['Status'] == 'Pending' and new_status in ['Processing', 'Ready to Deliver']:
            cursor.execute("""
                UPDATE Orders 
                SET Status = %s, EmployeeID = %s 
                WHERE OrderID = %s
            """, (new_status, employee_id, order_id))
            flash(f'Order status updated to {new_status} and assigned to you!', 'success')
        elif current_order['Status'] in ['Processing'] and new_status == 'Ready to Deliver':
            # Can change Processing to Ready to Deliver
            if not current_order['EmployeeID']:
                cursor.execute("""
                    UPDATE Orders 
                    SET Status = %s, EmployeeID = %s 
                    WHERE OrderID = %s
                """, (new_status, employee_id, order_id))
                flash(f'Order status updated to {new_status} and assigned to you!', 'success')
            else:
                cursor.execute("""
                    UPDATE Orders 
                    SET Status = %s 
                    WHERE OrderID = %s
                """, (new_status, order_id))
                flash(f'Order status updated to {new_status}!', 'success')
        elif current_order['EmployeeID'] == employee_id or session.get('role') == 'manager':
            # Employee already assigned or manager can change status
            cursor.execute("""
                UPDATE Orders 
                SET Status = %s 
                WHERE OrderID = %s
            """, (new_status, order_id))
            flash(f'Order status updated to {new_status}!', 'success')
        else:
            flash('You can only update orders assigned to you!', 'error')
            return redirect(url_for('order_details', order_id=order_id))
        
        conn.commit()
    except Error as e:
        flash(f'Error updating order status: {e}', 'error')
        conn.rollback()
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('order_details', order_id=order_id))

@app.route('/orders/<int:order_id>/update', methods=['GET', 'POST'])
@login_required
@role_required('employee', 'manager')
def update_order(order_id):
    """Update order details (employee/manager)"""
    conn = get_db_connection()
    if not conn:
        flash('Database connection failed!', 'error')
        return redirect(url_for('orders'))
    
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        # Get and validate input
        customer_id = request.form.get('customer_id', '').strip()
        employee_id = request.form.get('employee_id', '').strip() or None
        order_date = request.form.get('order_date', '').strip()
        total_amount = request.form.get('total_amount', '').strip()
        status = request.form.get('status', '').strip()
        
        # Validate required fields
        if not customer_id or not order_date or not status:
            flash('Please fill in all required fields!', 'error')
            return redirect(url_for('update_order', order_id=order_id))
        
        # Validate order date (allow future dates for orders)
        is_valid, error_msg = validate_date(order_date, 'Order date', allow_future=True)
        if not is_valid:
            flash(error_msg, 'error')
            return redirect(url_for('update_order', order_id=order_id))
        
        try:
            # Update order (TotalAmount is calculated from Order_Product)
            cursor.execute("""
                UPDATE Orders 
                SET CustomerID = %s, EmployeeID = %s, OrderDate = %s, Status = %s
                WHERE OrderID = %s
            """, (customer_id, employee_id, order_date, status, order_id))
            
            conn.commit()
            flash('Order updated successfully!', 'success')
            return redirect(url_for('order_details', order_id=order_id))
            
        except Error as e:
            flash(f'Error updating order: {e}', 'error')
            conn.rollback()
            return redirect(url_for('update_order', order_id=order_id))
        finally:
            cursor.close()
            conn.close()
    
    # GET request - show update form
    try:
        cursor.execute("""
            SELECT o.*, SUM(op.Quantity * op.PricePerUnit) as TotalAmount
            FROM Orders o
            LEFT JOIN Order_Product op ON o.OrderID = op.OrderID
            WHERE o.OrderID = %s
            GROUP BY o.OrderID, o.CustomerID, o.EmployeeID, o.OrderDate, o.Status
        """, (order_id,))
        order = cursor.fetchone()
        
        if not order:
            flash('Order not found!', 'error')
            return redirect(url_for('orders'))
        
        # Handle NULL TotalAmount
        if order.get('TotalAmount') is None:
            order['TotalAmount'] = 0
        
        # Get customers and employees for dropdowns
        cursor.execute("SELECT CustomerID, FirstName, LastName FROM Customers ORDER BY FirstName, LastName")
        customers = cursor.fetchall()
        
        cursor.execute("SELECT EmployeeID, FirstName, LastName FROM Employees ORDER BY FirstName, LastName")
        employees = cursor.fetchall()
        
    except Error as e:
        flash(f'Error loading order: {e}', 'error')
        return redirect(url_for('orders'))
    finally:
        cursor.close()
        conn.close()
    
    return render_template('update_order.html', order=order, customers=customers, employees=employees)

@app.route('/inventory')
def inventory():
    conn = get_db_connection()
    if not conn:
        flash('Database connection failed!', 'error')
        return render_template('inventory.html', products=[])
    
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT p.ProductID, p.ProductName, p.StockQuantity, p.SellingPrice,
                   p.CategoryName, s.SupplierName,
                   CASE 
                       WHEN p.StockQuantity < 10 THEN 'Low'
                       WHEN p.StockQuantity < 20 THEN 'Medium'
                       ELSE 'Good'
                   END as StockStatus
            FROM Products p
            LEFT JOIN Suppliers s ON p.SupplierID = s.SupplierID
            ORDER BY p.StockQuantity ASC, p.ProductName
        """)
        products = cursor.fetchall()
        
        cursor.execute("""
            SELECT SUM(StockQuantity * SellingPrice) as total_value
            FROM Products
        """)
        total_value = cursor.fetchone()['total_value'] or 0
        
    except Error as e:
        flash(f'Error fetching inventory: {e}', 'error')
        products = []
        total_value = 0
    finally:
        cursor.close()
        conn.close()
    
    return render_template('inventory.html', products=products, total_value=total_value)

@app.route('/reports')
@login_required
@role_required('manager')
def reports():
    conn = get_db_connection()
    if not conn:
        flash('Database connection failed!', 'error')
        return render_template('reports.html', reports={})
    
    cursor = conn.cursor(dictionary=True)
    reports = {}
    
    try:
        cursor.execute("""
            SELECT p.ProductName, SUM(op.Quantity) as TotalSold, SUM(op.Quantity * op.PricePerUnit) as Revenue
            FROM Order_Product op
            JOIN Products p ON op.ProductID = p.ProductID
            JOIN Orders o ON op.OrderID = o.OrderID
            WHERE o.Status = 'Completed'
            GROUP BY p.ProductID, p.ProductName
            ORDER BY TotalSold DESC
            LIMIT 5
        """)
        reports['top_products'] = cursor.fetchall()
        
        cursor.execute("""
            SELECT p.CategoryName, SUM(op.Quantity * op.PricePerUnit) as TotalRevenue,
                   SUM(op.Quantity) as TotalItems
            FROM Order_Product op
            JOIN Products p ON op.ProductID = p.ProductID
            JOIN Orders o ON op.OrderID = o.OrderID
            WHERE o.Status = 'Completed'
            GROUP BY p.CategoryName
            ORDER BY TotalRevenue DESC
        """)
        reports['sales_by_category'] = cursor.fetchall()
        
        cursor.execute("""
            SELECT e.EmployeeID, e.FirstName, e.LastName,
                   sales.OrderCount as OrderCount,
                   sales.TotalSales as TotalSales,
                   deliv.DeliveredOrders as DeliveredOrders,
                   deliv.DeliveredValue as DeliveredValue,
                   purch.ReceivedPurchases as ReceivedPurchases,
                   purch.TotalReceivedCost as TotalReceivedCost
            FROM Employees e
            LEFT JOIN (
                SELECT o.EmployeeID,
                       COUNT(DISTINCT o.OrderID) as OrderCount,
                       SUM(op.Quantity * op.PricePerUnit) as TotalSales
                FROM Orders o
                LEFT JOIN Order_Product op ON o.OrderID = op.OrderID
                GROUP BY o.EmployeeID
            ) sales ON e.EmployeeID = sales.EmployeeID
            LEFT JOIN (
                SELECT d.EmployeeID,
                       COUNT(DISTINCT d.OrderID) as DeliveredOrders,
                       SUM(op.Quantity * op.PricePerUnit) as DeliveredValue
                FROM Delivery d
                JOIN Orders o ON d.OrderID = o.OrderID
                LEFT JOIN Order_Product op ON o.OrderID = op.OrderID
                WHERE o.Status = 'Completed'
                GROUP BY d.EmployeeID
            ) deliv ON e.EmployeeID = deliv.EmployeeID
            LEFT JOIN (
                SELECT ReceivedBy as EmployeeID,
                       COUNT(*) as ReceivedPurchases,
                       SUM(TotalCost) as TotalReceivedCost
                FROM Purchases
                WHERE ReceivedBy IS NOT NULL
                GROUP BY ReceivedBy
            ) purch ON e.EmployeeID = purch.EmployeeID
            ORDER BY TotalSales DESC
        """)
        employee_perf = cursor.fetchall()
        for emp in employee_perf:
            if emp.get('OrderCount') is None:
                emp['OrderCount'] = 0
            if emp.get('TotalSales') is None:
                emp['TotalSales'] = 0
            if emp.get('DeliveredOrders') is None:
                emp['DeliveredOrders'] = 0
            if emp.get('DeliveredValue') is None:
                emp['DeliveredValue'] = 0
            if emp.get('ReceivedPurchases') is None:
                emp['ReceivedPurchases'] = 0
            if emp.get('TotalReceivedCost') is None:
                emp['TotalReceivedCost'] = 0
        reports['employee_performance'] = employee_perf
        
        cursor.execute("""
            SELECT DATE_FORMAT(o.OrderDate, '%Y-%m') as Month,
                   COUNT(DISTINCT o.OrderID) as OrderCount,
                   SUM(op.Quantity * op.PricePerUnit) as TotalSales
            FROM Orders o
            LEFT JOIN Order_Product op ON o.OrderID = op.OrderID
            WHERE o.Status = 'Completed'
            GROUP BY DATE_FORMAT(o.OrderDate, '%Y-%m')
            ORDER BY Month DESC
            LIMIT 6
        """)
        monthly_sales = cursor.fetchall()
        # Handle NULL TotalSales
        for month in monthly_sales:
            if month.get('TotalSales') is None:
                month['TotalSales'] = 0
        reports['monthly_sales'] = monthly_sales
        
    except Error as e:
        flash(f'Error generating reports: {e}', 'error')
    finally:
        cursor.close()
        conn.close()
    
    return render_template('reports.html', reports=reports)

# ==================== CUSTOMERS MANAGEMENT ====================

@app.route('/customers')
def customers():
    """Display all customers"""
    conn = get_db_connection()
    if not conn:
        flash('Database connection failed!', 'error')
        return render_template('customers.html', customers=[])
    
    cursor = conn.cursor(dictionary=True)
    search = request.args.get('search', '')
    
    try:
        query = """
            SELECT * FROM Customers
            WHERE 1=1
        """
        params = []
        
        if search:
            query += " AND (FirstName LIKE %s OR LastName LIKE %s OR Email LIKE %s OR PhoneNumber LIKE %s)"
            params.extend([f'%{search}%', f'%{search}%', f'%{search}%', f'%{search}%'])
        
        query += " ORDER BY FirstName, LastName"
        
        cursor.execute(query, params)
        customers = cursor.fetchall()
        
    except Error as e:
        flash(f'Error fetching customers: {e}', 'error')
        customers = []
    finally:
        cursor.close()
        conn.close()
    
    return render_template('customers.html', customers=customers, search=search)

@app.route('/customers/add', methods=['GET', 'POST'])
@login_required
@role_required('employee', 'manager')
def add_customer():
    """Add a new customer"""
    if request.method == 'POST':
        # Validate input
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        phone_number = request.form.get('phone_number', '').strip()
        
        # Validate first name
        is_valid, error_msg = validate_name(first_name, 'First name')
        if not is_valid:
            flash(error_msg, 'error')
            return redirect(url_for('add_customer'))
        
        # Validate last name
        is_valid, error_msg = validate_name(last_name, 'Last name')
        if not is_valid:
            flash(error_msg, 'error')
            return redirect(url_for('add_customer'))
        
        # Validate phone number
        if phone_number:
            is_valid, error_msg = validate_phone(phone_number)
            if not is_valid:
                flash(error_msg, 'error')
                return redirect(url_for('add_customer'))
        
        conn = get_db_connection()
        if not conn:
            flash('Database connection failed!', 'error')
            return redirect(url_for('customers'))
        
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO Customers (FirstName, LastName, Email, PhoneNumber, Address, RegistrationDate)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                first_name,
                last_name,
                request.form.get('email', '').strip() or None,
                phone_number or None,
                request.form.get('address', '').strip() or None,
                datetime.now().date()
            ))
            conn.commit()
            flash('Customer added successfully!', 'success')
            return redirect(url_for('customers'))
        except Error as e:
            flash(f'Error adding customer: {e}', 'error')
            conn.rollback()
        finally:
            cursor.close()
            conn.close()
    
    return render_template('add_customer.html')

@app.route('/customers/<int:customer_id>/update', methods=['GET', 'POST'])
def update_customer(customer_id):
    """Update an existing customer"""
    conn = get_db_connection()
    if not conn:
        flash('Database connection failed!', 'error')
        return redirect(url_for('customers'))
    
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        # Validate input
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        phone_number = request.form.get('phone_number', '').strip()
        
        # Validate first name
        is_valid, error_msg = validate_name(first_name, 'First name')
        if not is_valid:
            flash(error_msg, 'error')
            return redirect(url_for('update_customer', customer_id=customer_id))
        
        # Validate last name
        is_valid, error_msg = validate_name(last_name, 'Last name')
        if not is_valid:
            flash(error_msg, 'error')
            return redirect(url_for('update_customer', customer_id=customer_id))
        
        # Validate phone number
        if phone_number:
            is_valid, error_msg = validate_phone(phone_number)
            if not is_valid:
                flash(error_msg, 'error')
                return redirect(url_for('update_customer', customer_id=customer_id))
        
        try:
            cursor.execute("""
                UPDATE Customers
                SET FirstName = %s, LastName = %s, Email = %s, 
                    PhoneNumber = %s, Address = %s
                WHERE CustomerID = %s
            """, (
                first_name,
                last_name,
                request.form.get('email', '').strip() or None,
                phone_number or None,
                request.form.get('address', '').strip() or None,
                customer_id
            ))
            conn.commit()
            flash('Customer updated successfully!', 'success')
            return redirect(url_for('customers'))
        except Error as e:
            flash(f'Error updating customer: {e}', 'error')
            conn.rollback()
        finally:
            cursor.close()
            conn.close()
            return redirect(url_for('customers'))
    
    try:
        cursor.execute("SELECT * FROM Customers WHERE CustomerID = %s", (customer_id,))
        customer = cursor.fetchone()
        
        if not customer:
            flash('Customer not found!', 'error')
            return redirect(url_for('customers'))
        
    except Error as e:
        flash(f'Error loading customer: {e}', 'error')
        return redirect(url_for('customers'))
    finally:
        cursor.close()
        conn.close()
    
    return render_template('update_customer.html', customer=customer)

@app.route('/customers/<int:customer_id>/delete', methods=['POST'])
def delete_customer(customer_id):
    """Delete a customer"""
    conn = get_db_connection()
    if not conn:
        flash('Database connection failed!', 'error')
        return redirect(url_for('customers'))
    
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM Customers WHERE CustomerID = %s", (customer_id,))
        conn.commit()
        flash('Customer deleted successfully!', 'success')
    except Error as e:
        flash(f'Error deleting customer: {e}', 'error')
        conn.rollback()
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('customers'))

# ==================== SUPPLIERS MANAGEMENT ====================

@app.route('/suppliers')
@login_required
@role_required('employee', 'manager')
def suppliers():
    """Display all suppliers"""
    conn = get_db_connection()
    if not conn:
        flash('Database connection failed!', 'error')
        return render_template('suppliers.html', suppliers=[])
    
    cursor = conn.cursor(dictionary=True)
    search = request.args.get('search', '')
    
    try:
        query = """
            SELECT s.*, COUNT(p.ProductID) as ProductCount
            FROM Suppliers s
            LEFT JOIN Products p ON s.SupplierID = p.SupplierID
            WHERE 1=1
        """
        params = []
        
        if search:
            query += " AND (SupplierName LIKE %s OR ContactPerson LIKE %s OR Email LIKE %s OR PhoneNumber LIKE %s)"
            params.extend([f'%{search}%', f'%{search}%', f'%{search}%', f'%{search}%'])
        
        query += " GROUP BY s.SupplierID ORDER BY s.SupplierName"
        
        cursor.execute(query, params)
        suppliers = cursor.fetchall()
        
    except Error as e:
        flash(f'Error fetching suppliers: {e}', 'error')
        suppliers = []
    finally:
        cursor.close()
        conn.close()
    
    return render_template('suppliers.html', suppliers=suppliers, search=search)

@app.route('/suppliers/<int:supplier_id>')
@login_required
@role_required('employee', 'manager')
def supplier_details(supplier_id):
    """View supplier details and products"""
    conn = get_db_connection()
    if not conn:
        flash('Database connection failed!', 'error')
        return redirect(url_for('suppliers'))
    
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Get supplier information
        cursor.execute("""
            SELECT s.*, COUNT(p.ProductID) as ProductCount
            FROM Suppliers s
            LEFT JOIN Products p ON s.SupplierID = p.SupplierID
            WHERE s.SupplierID = %s
            GROUP BY s.SupplierID
        """, (supplier_id,))
        supplier = cursor.fetchone()
        
        if not supplier:
            flash('Supplier not found!', 'error')
            return redirect(url_for('suppliers'))
        
        # Get products from this supplier with purchase info
        cursor.execute("""
            SELECT p.ProductID, p.ProductName, p.SellingPrice, p.StockQuantity, 
                   p.Color, p.Material, p.Dimensions, p.DateAdded,
                   p.CategoryName,
                   MAX(pr.PurchaseDate) as LastPurchaseDate
            FROM Products p
            LEFT JOIN Purchase_Product pp ON p.ProductID = pp.ProductID
            LEFT JOIN Purchases pr ON pp.PurchaseID = pr.PurchaseID
            WHERE p.SupplierID = %s
            GROUP BY p.ProductID, p.ProductName, p.SellingPrice, p.StockQuantity, 
                     p.Color, p.Material, p.Dimensions, p.DateAdded, p.CategoryName
            ORDER BY p.ProductName
        """, (supplier_id,))
        products = cursor.fetchall()

        # Purchase stats for this supplier
        cursor.execute("""
            SELECT COUNT(DISTINCT p.PurchaseID) as PurchaseCount,
                   MAX(p.PurchaseDate) as LastPurchaseDate
            FROM Purchases p
            WHERE p.SupplierID = %s
        """, (supplier_id,))
        purchase_stats = cursor.fetchone()

    except Error as e:
        flash(f'Error fetching supplier details: {e}', 'error')
        return redirect(url_for('suppliers'))
    finally:
        cursor.close()
        conn.close()
    
    is_manager = session.get('role') == 'manager'
    return render_template('supplier_details.html', supplier=supplier, products=products,
                         purchase_stats=purchase_stats, is_manager=is_manager)

@app.route('/suppliers/add', methods=['GET', 'POST'])
@login_required
@role_required('employee', 'manager')
def add_supplier():
    """Add a new supplier"""
    if request.method == 'POST':
        # Validate input
        contact_person = request.form.get('contact_person', '').strip()
        phone_number = request.form.get('phone_number', '').strip()
        
        # Validate contact person (if provided)
        if contact_person:
            is_valid, error_msg = validate_name(contact_person, 'Contact person')
            if not is_valid:
                flash(error_msg, 'error')
                return redirect(url_for('add_supplier'))
        
        # Validate phone number (if provided)
        if phone_number:
            is_valid, error_msg = validate_phone(phone_number)
            if not is_valid:
                flash(error_msg, 'error')
                return redirect(url_for('add_supplier'))
        
        conn = get_db_connection()
        if not conn:
            flash('Database connection failed!', 'error')
            return redirect(url_for('suppliers'))
        
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO Suppliers (SupplierName, ContactPerson, PhoneNumber, Email)
                VALUES (%s, %s, %s, %s)
            """, (
                request.form.get('supplier_name', '').strip(),
                contact_person if contact_person else None,
                phone_number if phone_number else None,
                request.form.get('email', '').strip() or None
            ))
            conn.commit()
            flash('Supplier added successfully!', 'success')
            return redirect(url_for('suppliers'))
        except Error as e:
            flash(f'Error adding supplier: {e}', 'error')
            conn.rollback()
        finally:
            cursor.close()
            conn.close()
    
    return render_template('add_supplier.html')

@app.route('/suppliers/<int:supplier_id>/update', methods=['GET', 'POST'])
def update_supplier(supplier_id):
    """Update an existing supplier"""
    conn = get_db_connection()
    if not conn:
        flash('Database connection failed!', 'error')
        return redirect(url_for('suppliers'))
    
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        # Validate input
        contact_person = request.form.get('contact_person', '').strip()
        phone_number = request.form.get('phone_number', '').strip()
        
        # Validate contact person (if provided)
        if contact_person:
            is_valid, error_msg = validate_name(contact_person, 'Contact person')
            if not is_valid:
                flash(error_msg, 'error')
                return redirect(url_for('update_supplier', supplier_id=supplier_id))
        
        # Validate phone number (if provided)
        if phone_number:
            is_valid, error_msg = validate_phone(phone_number)
            if not is_valid:
                flash(error_msg, 'error')
                return redirect(url_for('update_supplier', supplier_id=supplier_id))
        
        try:
            cursor.execute("""
                UPDATE Suppliers
                SET SupplierName = %s, ContactPerson = %s, 
                    PhoneNumber = %s, Email = %s
                WHERE SupplierID = %s
            """, (
                request.form.get('supplier_name', '').strip(),
                contact_person if contact_person else None,
                phone_number if phone_number else None,
                request.form.get('email', '').strip() or None,
                supplier_id
            ))
            conn.commit()
            flash('Supplier updated successfully!', 'success')
            return redirect(url_for('suppliers'))
        except Error as e:
            flash(f'Error updating supplier: {e}', 'error')
            conn.rollback()
        finally:
            cursor.close()
            conn.close()
            return redirect(url_for('suppliers'))
    
    try:
        cursor.execute("SELECT * FROM Suppliers WHERE SupplierID = %s", (supplier_id,))
        supplier = cursor.fetchone()
        
        if not supplier:
            flash('Supplier not found!', 'error')
            return redirect(url_for('suppliers'))
        
    except Error as e:
        flash(f'Error loading supplier: {e}', 'error')
        return redirect(url_for('suppliers'))
    finally:
        cursor.close()
        conn.close()
    
    return render_template('update_supplier.html', supplier=supplier)

@app.route('/suppliers/<int:supplier_id>/delete', methods=['POST'])
def delete_supplier(supplier_id):
    """Delete a supplier"""
    conn = get_db_connection()
    if not conn:
        flash('Database connection failed!', 'error')
        return redirect(url_for('suppliers'))
    
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM Suppliers WHERE SupplierID = %s", (supplier_id,))
        conn.commit()
        flash('Supplier deleted successfully!', 'success')
    except Error as e:
        flash(f'Error deleting supplier: {e}', 'error')
        conn.rollback()
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('suppliers'))

# ==================== PURCHASES MANAGEMENT ====================

@app.route('/purchases')
@login_required
@role_required('employee', 'manager')
def purchases():
    """Display all purchases"""
    conn = get_db_connection()
    if not conn:
        flash('Database connection failed!', 'error')
        return render_template('purchases.html', purchases=[], is_manager=False)
    
    cursor = conn.cursor(dictionary=True)
    status_filter = request.args.get('status', '')
    search = request.args.get('search', '')
    
    try:
        query = """
            SELECT p.PurchaseID, p.PurchaseDate, p.TotalCost, p.ReceivedBy,
                   s.SupplierName,
                   e.FirstName as ReceivedByFirstName, e.LastName as ReceivedByLastName,
                   COUNT(pp.PurchaseDetailID) as ItemCount
            FROM Purchases p
            LEFT JOIN Suppliers s ON p.SupplierID = s.SupplierID
            LEFT JOIN Employees e ON p.ReceivedBy = e.EmployeeID
            LEFT JOIN Purchase_Product pp ON p.PurchaseID = pp.PurchaseID
            WHERE 1=1
        """
        params = []
        
        if status_filter == 'pending':
            query += " AND p.ReceivedBy IS NULL"
        elif status_filter == 'received':
            query += " AND p.ReceivedBy IS NOT NULL"
        
        if search:
            query += " AND (p.PurchaseID LIKE %s OR s.SupplierName LIKE %s)"
            params.extend([f'%{search}%', f'%{search}%'])
        
        query += """
            GROUP BY p.PurchaseID, p.PurchaseDate, p.TotalCost, p.ReceivedBy,
                     s.SupplierName, e.FirstName, e.LastName
            ORDER BY p.PurchaseDate DESC, p.PurchaseID DESC
        """
        
        cursor.execute(query, params)
        purchases = cursor.fetchall()
        
    except Error as e:
        flash(f'Error fetching purchases: {e}', 'error')
        purchases = []
    finally:
        cursor.close()
        conn.close()
    
    is_manager = session.get('role') == 'manager'
    return render_template('purchases.html', purchases=purchases, is_manager=is_manager,
                         status_filter=status_filter, search=search)

@app.route('/purchases/<int:purchase_id>')
@login_required
@role_required('employee', 'manager')
def purchase_details(purchase_id):
    """View purchase details"""
    conn = get_db_connection()
    if not conn:
        flash('Database connection failed!', 'error')
        return redirect(url_for('purchases'))
    
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT p.*, s.SupplierName,
                   e.FirstName as ReceivedByFirstName, e.LastName as ReceivedByLastName
            FROM Purchases p
            LEFT JOIN Suppliers s ON p.SupplierID = s.SupplierID
            LEFT JOIN Employees e ON p.ReceivedBy = e.EmployeeID
            WHERE p.PurchaseID = %s
        """, (purchase_id,))
        purchase = cursor.fetchone()
        
        if not purchase:
            flash('Purchase not found!', 'error')
            return redirect(url_for('purchases'))
        
        cursor.execute("""
            SELECT pp.PurchaseDetailID, pp.ProductID, pp.QuantityPurchased, pp.CostPerUnit,
                   pr.ProductName
            FROM Purchase_Product pp
            JOIN Products pr ON pp.ProductID = pr.ProductID
            WHERE pp.PurchaseID = %s
            ORDER BY pr.ProductName
        """, (purchase_id,))
        items = cursor.fetchall()
        
    except Error as e:
        flash(f'Error loading purchase: {e}', 'error')
        return redirect(url_for('purchases'))
    finally:
        cursor.close()
        conn.close()
    
    can_confirm = purchase.get('ReceivedBy') is None and session.get('role') in ['employee', 'manager']
    is_manager = session.get('role') == 'manager'
    return render_template('purchase_details.html', purchase=purchase, items=items,
                         can_confirm=can_confirm, is_manager=is_manager)

@app.route('/purchases/add', methods=['GET', 'POST'])
@login_required
@role_required('manager')
def add_purchase():
    """Add a new purchase (Manager only)"""
    conn = get_db_connection()
    if not conn:
        flash('Database connection failed!', 'error')
        return redirect(url_for('purchases'))
    
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        supplier_id = request.form.get('supplier_id')
        purchase_date = request.form.get('purchase_date') or datetime.now().date().strftime('%Y-%m-%d')
        items, error_msg = parse_purchase_items(request.form)
        
        if not supplier_id:
            flash('Supplier is required!', 'error')
            return redirect(url_for('add_purchase'))
        
        is_valid, date_error = validate_date(purchase_date, 'Purchase date', allow_future=False)
        if not is_valid:
            flash(date_error, 'error')
            return redirect(url_for('add_purchase'))
        
        if error_msg:
            flash(error_msg, 'error')
            return redirect(url_for('add_purchase'))
        
        try:
            cursor.execute("""
                SELECT ProductID, SupplierID, SellingPrice
                FROM Products
            """)
            product_rows = cursor.fetchall()
            product_map = {row['ProductID']: row for row in product_rows}
            
            supplier_id = int(supplier_id)
            total_cost = 0
            for item in items:
                product = product_map.get(item['product_id'])
                if not product:
                    flash('Invalid product selected!', 'error')
                    return redirect(url_for('add_purchase'))
                
                if supplier_id != product['SupplierID']:
                    flash('All items in a purchase must be from the same supplier.', 'error')
                    return redirect(url_for('add_purchase'))
                
                total_cost += item['quantity'] * (product['SellingPrice'] or 0)
            
            if supplier_id is None:
                flash('Products must have a supplier assigned.', 'error')
                return redirect(url_for('add_purchase'))
            
            cursor.execute("""
                INSERT INTO Purchases (SupplierID, PurchaseDate, TotalCost, ReceivedBy)
                VALUES (%s, %s, %s, NULL)
            """, (supplier_id, purchase_date, total_cost))
            purchase_id = cursor.lastrowid
            
            for item in items:
                product = product_map[item['product_id']]
                cost_per_unit = product['SellingPrice'] or 0
                cursor.execute("""
                    INSERT INTO Purchase_Product (PurchaseID, ProductID, QuantityPurchased, CostPerUnit)
                    VALUES (%s, %s, %s, %s)
                """, (purchase_id, item['product_id'], item['quantity'], cost_per_unit))
            
            conn.commit()
            flash('Purchase created successfully!', 'success')
            return redirect(url_for('purchase_details', purchase_id=purchase_id))
        except Error as e:
            flash(f'Error creating purchase: {e}', 'error')
            conn.rollback()
        finally:
            cursor.close()
            conn.close()
        
        return redirect(url_for('add_purchase'))
    
    try:
        cursor.execute("SELECT SupplierID, SupplierName FROM Suppliers ORDER BY SupplierName")
        suppliers = cursor.fetchall()
        cursor.execute("""
            SELECT p.ProductID, p.ProductName, p.SupplierID, s.SupplierName
            FROM Products p
            LEFT JOIN Suppliers s ON p.SupplierID = s.SupplierID
            ORDER BY p.ProductName
        """)
        products = cursor.fetchall()
    except Error as e:
        flash(f'Error loading form data: {e}', 'error')
        suppliers = []
        products = []
    finally:
        cursor.close()
        conn.close()
    
    today = datetime.now().date().strftime('%Y-%m-%d')
    return render_template('add_purchase.html', suppliers=suppliers, products=products, today=today)

@app.route('/purchases/<int:purchase_id>/update', methods=['GET', 'POST'])
@login_required
@role_required('manager')
def update_purchase(purchase_id):
    """Update a purchase (Manager only)"""
    conn = get_db_connection()
    if not conn:
        flash('Database connection failed!', 'error')
        return redirect(url_for('purchases'))
    
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        supplier_id = request.form.get('supplier_id')
        purchase_date = request.form.get('purchase_date') or datetime.now().date().strftime('%Y-%m-%d')
        items, error_msg = parse_purchase_items(request.form)
        
        if not supplier_id:
            flash('Supplier is required!', 'error')
            return redirect(url_for('update_purchase', purchase_id=purchase_id))
        
        is_valid, date_error = validate_date(purchase_date, 'Purchase date', allow_future=False)
        if not is_valid:
            flash(date_error, 'error')
            return redirect(url_for('update_purchase', purchase_id=purchase_id))
        
        if error_msg:
            flash(error_msg, 'error')
            return redirect(url_for('update_purchase', purchase_id=purchase_id))
        
        try:
            cursor.execute("SELECT ReceivedBy FROM Purchases WHERE PurchaseID = %s", (purchase_id,))
            purchase = cursor.fetchone()
            if not purchase:
                flash('Purchase not found!', 'error')
                return redirect(url_for('purchases'))
            if purchase.get('ReceivedBy'):
                flash('Cannot edit a purchase that has been received.', 'error')
                return redirect(url_for('purchase_details', purchase_id=purchase_id))
            
            cursor.execute("""
                SELECT ProductID, SupplierID, SellingPrice
                FROM Products
            """)
            product_rows = cursor.fetchall()
            product_map = {row['ProductID']: row for row in product_rows}
            
            supplier_id = int(supplier_id)
            total_cost = 0
            for item in items:
                product = product_map.get(item['product_id'])
                if not product:
                    flash('Invalid product selected!', 'error')
                    return redirect(url_for('update_purchase', purchase_id=purchase_id))
                
                if supplier_id != product['SupplierID']:
                    flash('All items in a purchase must be from the same supplier.', 'error')
                    return redirect(url_for('update_purchase', purchase_id=purchase_id))
                
                total_cost += item['quantity'] * (product['SellingPrice'] or 0)
            
            if supplier_id is None:
                flash('Products must have a supplier assigned.', 'error')
                return redirect(url_for('update_purchase', purchase_id=purchase_id))
            
            cursor.execute("""
                UPDATE Purchases
                SET SupplierID = %s, PurchaseDate = %s, TotalCost = %s
                WHERE PurchaseID = %s
            """, (supplier_id, purchase_date, total_cost, purchase_id))
            
            cursor.execute("DELETE FROM Purchase_Product WHERE PurchaseID = %s", (purchase_id,))
            for item in items:
                product = product_map[item['product_id']]
                cost_per_unit = product['SellingPrice'] or 0
                cursor.execute("""
                    INSERT INTO Purchase_Product (PurchaseID, ProductID, QuantityPurchased, CostPerUnit)
                    VALUES (%s, %s, %s, %s)
                """, (purchase_id, item['product_id'], item['quantity'], cost_per_unit))
            
            conn.commit()
            flash('Purchase updated successfully!', 'success')
            return redirect(url_for('purchase_details', purchase_id=purchase_id))
        except Error as e:
            flash(f'Error updating purchase: {e}', 'error')
            conn.rollback()
        finally:
            cursor.close()
            conn.close()
        
        return redirect(url_for('update_purchase', purchase_id=purchase_id))
    
    try:
        cursor.execute("""
            SELECT p.*, s.SupplierName
            FROM Purchases p
            LEFT JOIN Suppliers s ON p.SupplierID = s.SupplierID
            WHERE p.PurchaseID = %s
        """, (purchase_id,))
        purchase = cursor.fetchone()
        if not purchase:
            flash('Purchase not found!', 'error')
            return redirect(url_for('purchases'))
        if purchase.get('ReceivedBy'):
            flash('Cannot edit a purchase that has been received.', 'error')
            return redirect(url_for('purchase_details', purchase_id=purchase_id))
        
        cursor.execute("""
            SELECT pp.ProductID, pp.QuantityPurchased, pp.CostPerUnit
            FROM Purchase_Product pp
            WHERE pp.PurchaseID = %s
        """, (purchase_id,))
        items = cursor.fetchall()
        
        cursor.execute("SELECT SupplierID, SupplierName FROM Suppliers ORDER BY SupplierName")
        suppliers = cursor.fetchall()
        cursor.execute("""
            SELECT p.ProductID, p.ProductName, p.SupplierID, s.SupplierName
            FROM Products p
            LEFT JOIN Suppliers s ON p.SupplierID = s.SupplierID
            ORDER BY p.ProductName
        """)
        products = cursor.fetchall()
    except Error as e:
        flash(f'Error loading purchase: {e}', 'error')
        return redirect(url_for('purchases'))
    finally:
        cursor.close()
        conn.close()
    
    return render_template('update_purchase.html', purchase=purchase, items=items,
                         suppliers=suppliers, products=products)

@app.route('/purchases/<int:purchase_id>/delete', methods=['POST'])
@login_required
@role_required('manager')
def delete_purchase(purchase_id):
    """Delete a purchase (Manager only)"""
    conn = get_db_connection()
    if not conn:
        flash('Database connection failed!', 'error')
        return redirect(url_for('purchases'))
    
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT ReceivedBy FROM Purchases WHERE PurchaseID = %s", (purchase_id,))
        purchase = cursor.fetchone()
        if not purchase:
            flash('Purchase not found!', 'error')
            return redirect(url_for('purchases'))
        if purchase.get('ReceivedBy'):
            flash('Cannot delete a purchase that has been received.', 'error')
            return redirect(url_for('purchase_details', purchase_id=purchase_id))
        
        cursor.execute("DELETE FROM Purchases WHERE PurchaseID = %s", (purchase_id,))
        conn.commit()
        flash('Purchase deleted successfully!', 'success')
    except Error as e:
        flash(f'Error deleting purchase: {e}', 'error')
        conn.rollback()
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('purchases'))

@app.route('/purchases/<int:purchase_id>/receive', methods=['POST'])
@login_required
@role_required('employee', 'manager')
def receive_purchase(purchase_id):
    """Confirm a purchase as received and update stock"""
    conn = get_db_connection()
    if not conn:
        flash('Database connection failed!', 'error')
        return redirect(url_for('purchases'))
    
    cursor = conn.cursor(dictionary=True)
    employee_id = session.get('user_id')
    
    try:
        cursor.execute("SELECT ReceivedBy FROM Purchases WHERE PurchaseID = %s", (purchase_id,))
        purchase = cursor.fetchone()
        if not purchase:
            flash('Purchase not found!', 'error')
            return redirect(url_for('purchases'))
        if purchase.get('ReceivedBy'):
            flash('This purchase has already been received.', 'error')
            return redirect(url_for('purchase_details', purchase_id=purchase_id))
        
        cursor.execute("""
            SELECT ProductID, QuantityPurchased
            FROM Purchase_Product
            WHERE PurchaseID = %s
        """, (purchase_id,))
        items = cursor.fetchall()
        
        for item in items:
            cursor.execute("""
                UPDATE Products
                SET StockQuantity = StockQuantity + %s
                WHERE ProductID = %s
            """, (item['QuantityPurchased'], item['ProductID']))
        
        cursor.execute("""
            UPDATE Purchases
            SET ReceivedBy = %s
            WHERE PurchaseID = %s
        """, (employee_id, purchase_id))
        
        conn.commit()
        flash('Purchase marked as received and stock updated.', 'success')
    except Error as e:
        flash(f'Error receiving purchase: {e}', 'error')
        conn.rollback()
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('purchase_details', purchase_id=purchase_id))

# ==================== EMPLOYEE MANAGEMENT (MANAGER ONLY) ====================

@app.route('/employees')
@login_required
@role_required('manager')
def employees():
    """Display all employees (Manager only)"""
    conn = get_db_connection()
    if not conn:
        flash('Database connection failed!', 'error')
        return render_template('employees.html', employees=[])
    
    cursor = conn.cursor(dictionary=True)
    search = request.args.get('search', '')
    
    try:
        query = """
            SELECT e.*, 
                   COUNT(DISTINCT o.OrderID) as OrderCount,
                   SUM(op.Quantity * op.PricePerUnit) as TotalSales
            FROM Employees e
            LEFT JOIN Orders o ON e.EmployeeID = o.EmployeeID
            LEFT JOIN Order_Product op ON o.OrderID = op.OrderID
            WHERE 1=1
        """
        params = []
        
        if search:
            query += " AND (e.FirstName LIKE %s OR e.LastName LIKE %s OR e.Email LIKE %s OR e.Position LIKE %s OR e.PhoneNumber LIKE %s)"
            params.extend([f'%{search}%', f'%{search}%', f'%{search}%', f'%{search}%',f'%{search}%'])
        
        query += " GROUP BY e.EmployeeID, e.FirstName, e.LastName, e.Position, e.HireDate, e.Salary, e.PhoneNumber, e.Email ORDER BY e.FirstName, e.LastName"
        
        cursor.execute(query, params)
        employees = cursor.fetchall()
        # Handle NULL TotalSales
        for emp in employees:
            if emp.get('TotalSales') is None:
                emp['TotalSales'] = 0
        
    except Error as e:
        flash(f'Error fetching employees: {e}', 'error')
        employees = []
    finally:
        cursor.close()
        conn.close()
    
    return render_template('employees.html', employees=employees, search=search)

@app.route('/employees/<int:employee_id>')
@login_required
@role_required('manager')
def employee_details(employee_id):
    """View employee details (Manager only)"""
    conn = get_db_connection()
    if not conn:
        flash('Database connection failed!', 'error')
        return redirect(url_for('employees'))
    
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT * FROM Employees WHERE EmployeeID = %s", (employee_id,))
        employee = cursor.fetchone()
        
        if not employee:
            flash('Employee not found!', 'error')
            return redirect(url_for('employees'))
        
        if employee.get('Position') == 'Delivery Staff':
            cursor.execute("""
                SELECT COUNT(DISTINCT d.OrderID) as OrderCount,
                       SUM(op.Quantity * op.PricePerUnit) as TotalSales
                FROM Delivery d
                JOIN Orders o ON d.OrderID = o.OrderID
                LEFT JOIN Order_Product op ON o.OrderID = op.OrderID
                WHERE d.EmployeeID = %s
            """, (employee_id,))
            stats = cursor.fetchone()
            
            cursor.execute("""
                SELECT o.*, c.FirstName, c.LastName, c.Email, c.PhoneNumber,
                       SUM(op.Quantity * op.PricePerUnit) as TotalAmount
                FROM Delivery d
                JOIN Orders o ON d.OrderID = o.OrderID
                LEFT JOIN Customers c ON o.CustomerID = c.CustomerID
                LEFT JOIN Order_Product op ON o.OrderID = op.OrderID
                WHERE d.EmployeeID = %s
                GROUP BY o.OrderID, o.CustomerID, o.EmployeeID, o.OrderDate, o.Status,
                         c.FirstName, c.LastName, c.Email, c.PhoneNumber
                ORDER BY o.OrderDate DESC
                LIMIT 10
            """, (employee_id,))
            orders = cursor.fetchall()
        else:
            cursor.execute("""
                SELECT COUNT(DISTINCT o.OrderID) as OrderCount,
                       SUM(op.Quantity * op.PricePerUnit) as TotalSales
                FROM Orders o
                LEFT JOIN Order_Product op ON o.OrderID = op.OrderID
                WHERE o.EmployeeID = %s
            """, (employee_id,))
            stats = cursor.fetchone()
            
            cursor.execute("""
                SELECT o.*, c.FirstName, c.LastName, c.Email, c.PhoneNumber,
                       SUM(op.Quantity * op.PricePerUnit) as TotalAmount
                FROM Orders o
                LEFT JOIN Customers c ON o.CustomerID = c.CustomerID
                LEFT JOIN Order_Product op ON o.OrderID = op.OrderID
                WHERE o.EmployeeID = %s
                GROUP BY o.OrderID, o.CustomerID, o.EmployeeID, o.OrderDate, o.Status,
                         c.FirstName, c.LastName, c.Email, c.PhoneNumber
                ORDER BY o.OrderDate DESC
                LIMIT 10
            """, (employee_id,))
            orders = cursor.fetchall()
        
        employee['OrderCount'] = stats.get('OrderCount') if stats else 0
        employee['TotalSales'] = stats.get('TotalSales') or 0
        # Handle NULL TotalAmount
        for order in orders:
            if order.get('TotalAmount') is None:
                order['TotalAmount'] = 0
        
    except Error as e:
        flash(f'Error fetching employee details: {e}', 'error')
        return redirect(url_for('employees'))
    finally:
        cursor.close()
        conn.close()
    
    return render_template('employee_details.html', employee=employee, orders=orders)

@app.route('/employees/add', methods=['GET', 'POST'])
@login_required
@role_required('manager')
def add_employee():
    """Add a new employee (Manager only)"""
    conn = get_db_connection()
    if not conn:
        flash('Database connection failed!', 'error')
        return redirect(url_for('employees'))
    
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        # Validate input
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        position = request.form.get('position', '').strip()
        hire_date = request.form.get('hire_date', '').strip()
        salary = request.form.get('salary', '').strip()
        phone_number = request.form.get('phone_number', '').strip()
        
        # Validate first name
        is_valid, error_msg = validate_name(first_name, 'First name')
        if not is_valid:
            flash(error_msg, 'error')
            return redirect(url_for('add_employee'))
        
        # Validate last name
        is_valid, error_msg = validate_name(last_name, 'Last name')
        if not is_valid:
            flash(error_msg, 'error')
            return redirect(url_for('add_employee'))
        
        # Validate position
        is_valid, error_msg = validate_position(position)
        if not is_valid:
            flash(error_msg, 'error')
            return redirect(url_for('add_employee'))
        
        # Validate hire date
        if hire_date:
            is_valid, error_msg = validate_date(hire_date, 'Hire date')
            if not is_valid:
                flash(error_msg, 'error')
                return redirect(url_for('add_employee'))
        
        # Validate salary
        if salary:
            is_valid, error_msg = validate_salary(salary)
            if not is_valid:
                flash(error_msg, 'error')
                return redirect(url_for('add_employee'))
        
        # Validate phone number
        if phone_number:
            is_valid, error_msg = validate_phone(phone_number)
            if not is_valid:
                flash(error_msg, 'error')
                return redirect(url_for('add_employee'))
        
        try:
            cursor.execute("""
                INSERT INTO Employees (FirstName, LastName, Position, HireDate, Salary, PhoneNumber, Email)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                first_name,
                last_name,
                position,
                hire_date if hire_date else None,
                float(salary) if salary else None,
                phone_number if phone_number else None,
                request.form.get('email', '').strip() or None
            ))
            conn.commit()
            flash('Employee added successfully!', 'success')
            return redirect(url_for('employees'))
        except Error as e:
            flash(f'Error adding employee: {e}', 'error')
            conn.rollback()
        finally:
            cursor.close()
            conn.close()
    
    return render_template('add_employee.html')

@app.route('/employees/<int:employee_id>/update', methods=['GET', 'POST'])
@login_required
@role_required('manager')
def update_employee(employee_id):
    """Update an existing employee (Manager only)"""
    conn = get_db_connection()
    if not conn:
        flash('Database connection failed!', 'error')
        return redirect(url_for('employees'))
    
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        # Validate input
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        position = request.form.get('position', '').strip()
        hire_date = request.form.get('hire_date', '').strip()
        salary = request.form.get('salary', '').strip()
        phone_number = request.form.get('phone_number', '').strip()
        
        # Validate first name
        is_valid, error_msg = validate_name(first_name, 'First name')
        if not is_valid:
            flash(error_msg, 'error')
            return redirect(url_for('update_employee', employee_id=employee_id))
        
        # Validate last name
        is_valid, error_msg = validate_name(last_name, 'Last name')
        if not is_valid:
            flash(error_msg, 'error')
            return redirect(url_for('update_employee', employee_id=employee_id))
        
        # Validate position
        is_valid, error_msg = validate_position(position)
        if not is_valid:
            flash(error_msg, 'error')
            return redirect(url_for('update_employee', employee_id=employee_id))
        
        # Validate hire date
        if hire_date:
            is_valid, error_msg = validate_date(hire_date, 'Hire date')
            if not is_valid:
                flash(error_msg, 'error')
                return redirect(url_for('update_employee', employee_id=employee_id))
        
        # Validate salary
        if salary:
            is_valid, error_msg = validate_salary(salary)
            if not is_valid:
                flash(error_msg, 'error')
                return redirect(url_for('update_employee', employee_id=employee_id))
        
        # Validate phone number
        if phone_number:
            is_valid, error_msg = validate_phone(phone_number)
            if not is_valid:
                flash(error_msg, 'error')
                return redirect(url_for('update_employee', employee_id=employee_id))
        
        try:
            cursor.execute("""
                UPDATE Employees
                SET FirstName = %s, LastName = %s, Position = %s, 
                    HireDate = %s, Salary = %s, PhoneNumber = %s, Email = %s
                WHERE EmployeeID = %s
            """, (
                first_name,
                last_name,
                position,
                hire_date if hire_date else None,
                float(salary) if salary else None,
                phone_number if phone_number else None,
                request.form.get('email', '').strip() or None,
                employee_id
            ))
            conn.commit()
            flash('Employee updated successfully!', 'success')
            return redirect(url_for('employees'))
        except Error as e:
            flash(f'Error updating employee: {e}', 'error')
            conn.rollback()
        finally:
            cursor.close()
            conn.close()
            return redirect(url_for('employees'))
    
    try:
        cursor.execute("SELECT * FROM Employees WHERE EmployeeID = %s", (employee_id,))
        employee = cursor.fetchone()
        
        if not employee:
            flash('Employee not found!', 'error')
            return redirect(url_for('employees'))
        
    except Error as e:
        flash(f'Error loading employee: {e}', 'error')
        return redirect(url_for('employees'))
    finally:
        cursor.close()
        conn.close()
    
    return render_template('update_employee.html', employee=employee)

@app.route('/employees/<int:employee_id>/delete', methods=['POST'])
@login_required
@role_required('manager')
def delete_employee(employee_id):
    """Delete an employee (Manager only)"""
    conn = get_db_connection()
    if not conn:
        flash('Database connection failed!', 'error')
        return redirect(url_for('employees'))
    
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Check if employee exists
        cursor.execute("SELECT FirstName, LastName FROM Employees WHERE EmployeeID = %s", (employee_id,))
        employee = cursor.fetchone()
        
        if not employee:
            flash('Employee not found!', 'error')
            return redirect(url_for('employees'))
        
        # Check if employee is assigned to any orders
        cursor.execute("SELECT COUNT(*) as count FROM Orders WHERE EmployeeID = %s", (employee_id,))
        order_count = cursor.fetchone()['count']
        
        if order_count > 0:
            flash(f'Cannot delete employee "{employee["FirstName"]} {employee["LastName"]}" because they are assigned to {order_count} order(s)!', 'error')
            return redirect(url_for('employees'))
        
        # Delete the employee
        cursor.execute("DELETE FROM Employees WHERE EmployeeID = %s", (employee_id,))
        conn.commit()
        flash(f'Employee "{employee["FirstName"]} {employee["LastName"]}" deleted successfully!', 'success')
        
    except Error as e:
        flash(f'Error deleting employee: {e}', 'error')
        conn.rollback()
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('employees'))

# ==================== CREATE NEW ORDER ====================

@app.route('/orders/create', methods=['GET', 'POST'])
def create_order():
    """Create a new order"""
    conn = get_db_connection()
    if not conn:
        flash('Database connection failed!', 'error')
        return redirect(url_for('orders'))
    
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        try:
            customer_id = int(request.form['customer_id'])
            employee_id = int(request.form['employee_id']) if request.form['employee_id'] else None
            order_date = datetime.now().date()
            
            # Get product quantities from form
            product_ids = request.form.getlist('product_id[]')
            quantities = request.form.getlist('quantity[]')
            
            if not product_ids or not all(quantities):
                flash('Please add at least one product to the order!', 'error')
                return redirect(url_for('create_order'))
            
            # Calculate total amount
            total_amount = 0
            order_items = []
            
            for product_id, quantity in zip(product_ids, quantities):
                if quantity and int(quantity) > 0:
                    cursor.execute("SELECT SellingPrice FROM Products WHERE ProductID = %s", (product_id,))
                    product = cursor.fetchone()
                    if product:
                        price = product['SellingPrice']
                        qty = int(quantity)
                        total_amount += price * qty
                        order_items.append({
                            'product_id': product_id,
                            'quantity': qty,
                            'price': price
                        })
            
            if total_amount == 0:
                flash('Invalid order - total amount is zero!', 'error')
                return redirect(url_for('create_order'))
            
            # Create the order
            cursor.execute("""
                INSERT INTO Orders (CustomerID, EmployeeID, OrderDate, Status)
                VALUES (%s, %s, %s, 'Pending')
            """, (customer_id, employee_id, order_date))
            
            order_id = cursor.lastrowid
            
            # Add order products
            for item in order_items:
                cursor.execute("""
                    INSERT INTO Order_Product (OrderID, ProductID, Quantity, PricePerUnit)
                    VALUES (%s, %s, %s, %s)
                """, (order_id, item['product_id'], item['quantity'], item['price']))
                
                # Update product stock
                cursor.execute("""
                    UPDATE Products 
                    SET StockQuantity = StockQuantity - %s 
                    WHERE ProductID = %s
                """, (item['quantity'], item['product_id']))
            
            conn.commit()
            flash(f'Order #{order_id} created successfully!', 'success')
            return redirect(url_for('order_details', order_id=order_id))
            
        except Error as e:
            flash(f'Error creating order: {e}', 'error')
            conn.rollback()
        finally:
            cursor.close()
            conn.close()
            return redirect(url_for('create_order'))
    
    try:
        # Get customers for dropdown
        cursor.execute("SELECT CustomerID, FirstName, LastName FROM Customers ORDER BY LastName, FirstName")
        customers = cursor.fetchall()
        
        # Get employees for dropdown
        cursor.execute("SELECT EmployeeID, FirstName, LastName FROM Employees WHERE Position IN ('Sales Associate', 'Manager') ORDER BY LastName, FirstName")
        employees = cursor.fetchall()
        
        # Get products with stock > 0
        cursor.execute("""
            SELECT p.*
            FROM Products p
            WHERE p.StockQuantity > 0
            ORDER BY p.ProductName
        """)
        products = cursor.fetchall()
        
    except Error as e:
        flash(f'Error loading data: {e}', 'error')
        customers = []
        employees = []
        products = []
    finally:
        cursor.close()
        conn.close()
    
    return render_template('create_order.html', 
                         customers=customers, 
                         employees=employees, 
                         products=products)

# ==================== DELIVERY STAFF ROUTES ====================

@app.route('/delivery/dashboard')
@login_required
@role_required('delivery_staff')
def delivery_dashboard():
    """Delivery staff dashboard - shows orders that need delivery"""
    conn = get_db_connection()
    if not conn:
        flash('Database connection failed!', 'error')
        return render_template('delivery/dashboard.html', orders=[], my_deliveries=[])
    
    cursor = conn.cursor(dictionary=True)
    employee_id = session.get('user_id')
    
    try:
        # Get orders that are ready to deliver
        cursor.execute("""
            SELECT DISTINCT o.OrderID, o.OrderDate, o.Status as OrderStatus,
                   SUM(op.Quantity * op.PricePerUnit) as TotalAmount,
                   c.FirstName, c.LastName, c.PhoneNumber, c.Email,
                   d.OrderID as DeliveryOrderID, d.DeliveryAddress, d.ScheduledDate, d.DeliveryDate, 
                   d.EmployeeID as AssignedEmployeeID
            FROM Orders o
            LEFT JOIN Customers c ON o.CustomerID = c.CustomerID
            LEFT JOIN Delivery d ON o.OrderID = d.OrderID
            LEFT JOIN Order_Product op ON o.OrderID = op.OrderID
            WHERE o.Status = 'Ready to Deliver'
            GROUP BY o.OrderID, o.OrderDate, o.Status, c.FirstName, c.LastName, c.PhoneNumber, c.Email,
                     d.OrderID, d.DeliveryAddress, d.ScheduledDate, d.DeliveryDate, d.EmployeeID
            ORDER BY o.OrderDate DESC
        """)
        available_orders = cursor.fetchall()
        # Handle NULL TotalAmount
        for order in available_orders:
            if order.get('TotalAmount') is None:
                order['TotalAmount'] = 0
        
        # Get my assigned deliveries (orders I'm delivering - status Scheduled for Delivery or Ready to Deliver)
        cursor.execute("""
            SELECT d.*, o.OrderDate, o.Status as OrderStatus,
                   SUM(op.Quantity * op.PricePerUnit) as TotalAmount,
                   c.FirstName, c.LastName, c.PhoneNumber, c.Email
            FROM Delivery d
            JOIN Orders o ON d.OrderID = o.OrderID
            LEFT JOIN Customers c ON o.CustomerID = c.CustomerID
            LEFT JOIN Order_Product op ON o.OrderID = op.OrderID
            WHERE d.EmployeeID = %s AND o.Status IN ('Ready to Deliver', 'Scheduled for Delivery')
            GROUP BY d.OrderID, o.OrderDate, o.Status, c.FirstName, c.LastName, c.PhoneNumber, c.Email,
                     d.EmployeeID, d.DeliveryAddress, d.ScheduledDate, d.DeliveryDate
            ORDER BY d.ScheduledDate DESC
        """, (employee_id,))
        my_deliveries = cursor.fetchall()
        for delivery in my_deliveries:
            if delivery.get('TotalAmount') is None:
                delivery['TotalAmount'] = 0
        
        # Get my completed deliveries (for statistics)
        cursor.execute("""
            SELECT COUNT(*) as CompletedCount
            FROM Delivery d
            JOIN Orders o ON d.OrderID = o.OrderID
            WHERE d.EmployeeID = %s AND o.Status = 'Completed'
        """, (employee_id,))
        completed_stats = cursor.fetchone()
        
    except Error as e:
        flash(f'Error fetching delivery orders: {e}', 'error')
        available_orders = []
        my_deliveries = []
    finally:
        cursor.close()
        conn.close()
    
    return render_template('delivery/dashboard.html', orders=available_orders, my_deliveries=my_deliveries, completed_count=completed_stats.get('CompletedCount', 0) if completed_stats else 0)

@app.route('/delivery/order/<int:order_id>')
@login_required
@role_required('delivery_staff')
def delivery_order_details(order_id):
    """View order details for delivery"""
    conn = get_db_connection()
    if not conn:
        flash('Database connection failed!', 'error')
        return redirect(url_for('delivery_dashboard'))
    
    cursor = conn.cursor(dictionary=True)
    employee_id = session.get('user_id')
    
    try:
        # Get order details
        cursor.execute("""
            SELECT o.*, c.FirstName, c.LastName, c.Email, c.PhoneNumber, c.Address as CustomerAddress,
                   d.OrderID as DeliveryOrderID, d.DeliveryAddress, d.ScheduledDate, d.DeliveryDate, 
                   d.EmployeeID as AssignedEmployeeID,
                   SUM(op.Quantity * op.PricePerUnit) as TotalAmount
            FROM Orders o
            LEFT JOIN Customers c ON o.CustomerID = c.CustomerID
            LEFT JOIN Delivery d ON o.OrderID = d.OrderID
            LEFT JOIN Order_Product op ON o.OrderID = op.OrderID
            WHERE o.OrderID = %s
            GROUP BY o.OrderID, o.CustomerID, o.EmployeeID, o.OrderDate, o.Status,
                     c.FirstName, c.LastName, c.Email, c.PhoneNumber, c.Address,
                     d.OrderID, d.DeliveryAddress, d.ScheduledDate, d.DeliveryDate, d.EmployeeID
        """, (order_id,))
        order = cursor.fetchone()
        
        if not order:
            flash('Order not found!', 'error')
            return redirect(url_for('delivery_dashboard'))
        
        # Handle NULL TotalAmount
        if order.get('TotalAmount') is None:
            order['TotalAmount'] = 0
        
        # Get order products
        cursor.execute("""
            SELECT op.*, p.ProductName, p.Dimensions, p.Color, p.Material
            FROM Order_Product op
            JOIN Products p ON op.ProductID = p.ProductID
            WHERE op.OrderID = %s
        """, (order_id,))
        order_products = cursor.fetchall()
        
    except Error as e:
        flash(f'Error fetching order details: {e}', 'error')
        return redirect(url_for('delivery_dashboard'))
    finally:
        cursor.close()
        conn.close()
    
    is_assigned = order.get('AssignedEmployeeID') == employee_id if order.get('AssignedEmployeeID') else False
    return render_template('delivery/order_details.html', order=order, order_products=order_products, is_assigned=is_assigned)

@app.route('/delivery/order/<int:order_id>/take', methods=['POST'])
@login_required
@role_required('delivery_staff')
def delivery_take_order(order_id):
    """Assign delivery staff to an order"""
    conn = get_db_connection()
    if not conn:
        flash('Database connection failed!', 'error')
        return redirect(url_for('delivery_dashboard'))
    
    cursor = conn.cursor(dictionary=True)
    employee_id = session.get('user_id')
    
    try:
        # Check order status - must be "Ready to Deliver"
        cursor.execute("SELECT Status FROM Orders WHERE OrderID = %s", (order_id,))
        order = cursor.fetchone()
        
        if not order:
            flash('Order not found!', 'error')
            return redirect(url_for('delivery_dashboard'))
        
        if order['Status'] != 'Ready to Deliver':
            flash('Only orders with status "Ready to Deliver" can be assigned for delivery!', 'error')
            return redirect(url_for('delivery_order_details', order_id=order_id))
        
        # Check if delivery record exists
        cursor.execute("SELECT OrderID, EmployeeID FROM Delivery WHERE OrderID = %s", (order_id,))
        delivery = cursor.fetchone()
        
        if delivery:
            # Update existing delivery record (only if not already assigned to someone else)
            if delivery['EmployeeID'] is None or delivery['EmployeeID'] == employee_id:
                cursor.execute("""
                    UPDATE Delivery 
                    SET EmployeeID = %s
                    WHERE OrderID = %s
                """, (employee_id, order_id))
            else:
                flash('This order is already assigned to another delivery staff member!', 'error')
                return redirect(url_for('delivery_order_details', order_id=order_id))
        else:
            # Create new delivery record - get customer address if available
            cursor.execute("""
                SELECT c.Address as CustomerAddress
                FROM Orders o
                LEFT JOIN Customers c ON o.CustomerID = c.CustomerID
                WHERE o.OrderID = %s
            """, (order_id,))
            order_data = cursor.fetchone()
            
            delivery_address = order_data['CustomerAddress'] if order_data and order_data.get('CustomerAddress') else None
            
            cursor.execute("""
                INSERT INTO Delivery (OrderID, EmployeeID, DeliveryAddress, ScheduledDate)
                VALUES (%s, %s, %s, %s)
            """, (order_id, employee_id, delivery_address, datetime.now().date()))
        
        # Update order status to "Scheduled for Delivery" when delivery staff takes it
        cursor.execute("""
            UPDATE Orders 
            SET Status = 'Scheduled for Delivery'
            WHERE OrderID = %s
        """, (order_id,))
        
        conn.commit()
        flash(f'You have been assigned to deliver Order #{order_id}! Order status updated to "Scheduled for Delivery".', 'success')
        
    except Error as e:
        flash(f'Error taking order: {e}', 'error')
        conn.rollback()
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('delivery_order_details', order_id=order_id))

@app.route('/delivery/order/<int:order_id>/update', methods=['POST'])
@login_required
@role_required('delivery_staff')
def delivery_update_order(order_id):
    """Update delivery status and date"""
    conn = get_db_connection()
    if not conn:
        flash('Database connection failed!', 'error')
        return redirect(url_for('delivery_dashboard'))
    
    cursor = conn.cursor(dictionary=True)
    employee_id = session.get('user_id')
    
    try:
        delivery_status = request.form.get('delivery_status')
        delivery_date = request.form.get('delivery_date')
        scheduled_date = request.form.get('scheduled_date')
        
        # Validate delivery date if provided
        # For "Delivered" status, only allow today or past dates (delivery cannot be in future)
        # For "Scheduled for Delivery", date must be today or future
        if delivery_date:
            # First check basic date format
            is_valid, error_msg = validate_date(delivery_date, 'Delivery date', allow_future=False)
            if is_valid:
                try:
                    date_obj = datetime.strptime(delivery_date.strip(), '%Y-%m-%d').date()
                    today = datetime.now().date()
                    
                    if delivery_status == 'Delivered':
                        # For "Delivered", date cannot be in the future - only today or past
                        if date_obj > today:
                            is_valid = False
                            error_msg = 'Delivery date cannot be in the future! Must be today or a past date.'
                    elif delivery_status == 'Scheduled for Delivery':
                        # For "Scheduled for Delivery", date must be today or future
                        if date_obj < today:
                            is_valid = False
                            error_msg = 'Delivery date cannot be in the past! Must be today or a future date.'
                except ValueError:
                    pass  # Already handled by validate_date
            
            if not is_valid:
                flash(error_msg, 'error')
                return redirect(url_for('delivery_order_details', order_id=order_id))
        
        # Validate scheduled date - must be today or future
        if scheduled_date:
            is_valid, error_msg = validate_date(scheduled_date, 'Scheduled date', allow_future=True)
            if not is_valid:
                flash(error_msg, 'error')
                return redirect(url_for('delivery_order_details', order_id=order_id))
        
        # Get delivery record
        cursor.execute("SELECT OrderID, EmployeeID FROM Delivery WHERE OrderID = %s", (order_id,))
        delivery = cursor.fetchone()
        
        if not delivery or delivery['EmployeeID'] != employee_id:
            flash('You are not assigned to this delivery!', 'error')
            return redirect(url_for('delivery_dashboard'))
        
        # Map delivery status to order status
        # Delivery staff can only set delivery_status to "Scheduled for Delivery" or mark as delivered (Completed)
        if delivery_status not in ['Scheduled for Delivery', 'Delivered']:
            flash('Invalid delivery status! You can only set status to "Scheduled for Delivery" or "Delivered".', 'error')
            return redirect(url_for('delivery_order_details', order_id=order_id))
        
        # Validate that dates are only set when appropriate status is selected
        if scheduled_date and delivery_status != 'Scheduled for Delivery':
            flash('Scheduled date can only be set when status is "Scheduled for Delivery"!', 'error')
            return redirect(url_for('delivery_order_details', order_id=order_id))
        
        if delivery_date and delivery_status != 'Delivered':
            flash('Delivery date can only be set when status is "Delivered"!', 'error')
            return redirect(url_for('delivery_order_details', order_id=order_id))
        
        # Update delivery record (dates only, status is in Orders table)
        update_query = "UPDATE Delivery SET"
        params = []
        
        # Only set delivery_date if status is "Delivered"
        if delivery_date and delivery_status == 'Delivered':
            update_query += " DeliveryDate = %s"
            params.append(delivery_date)
        
        # Only set scheduled_date if status is "Scheduled for Delivery"
        if scheduled_date and delivery_status == 'Scheduled for Delivery':
            if params:
                update_query += ", ScheduledDate = %s"
            else:
                update_query += " ScheduledDate = %s"
            params.append(scheduled_date)
        
        # Update order status based on delivery status
        if delivery_status == 'Scheduled for Delivery':
            # Change order status to "Scheduled for Delivery"
            cursor.execute("UPDATE Orders SET Status = 'Scheduled for Delivery' WHERE OrderID = %s", (order_id,))
        elif delivery_status == 'Delivered':
            # Set delivery date to today if not provided
            if not delivery_date:
                if params:
                    update_query += ", DeliveryDate = %s"
                else:
                    update_query += " DeliveryDate = %s"
                params.append(datetime.now().date())
            # Update order status to Completed
            cursor.execute("UPDATE Orders SET Status = 'Completed' WHERE OrderID = %s", (order_id,))
        
        # Only update delivery table if there are date parameters
        if params:
            params.append(order_id)
            update_query += " WHERE OrderID = %s"
            cursor.execute(update_query, params)
        conn.commit()
        
        status_messages = {
            'Scheduled for Delivery': 'Order status updated to Scheduled for Delivery!',
            'Delivered': 'Delivery completed! Order marked as completed and added to your deliveries.'
        }
        flash(status_messages.get(delivery_status, 'Delivery updated successfully!'), 'success')
        
    except Error as e:
        flash(f'Error updating delivery: {e}', 'error')
        conn.rollback()
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('delivery_order_details', order_id=order_id))

if __name__ == '__main__':
    print("\n AMIN Furniture Store - Database Management System")
    print(" Students: Malak Milhem - Layal Hajji")
    print(" Access the application at: http://localhost:5000\n")
    app.run(debug=True, host='0.0.0.0', port=5000)
