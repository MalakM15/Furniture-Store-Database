"""
AMIN Furniture Store - Database Management System
Student IDs: 1220031_1220871

"""

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import mysql.connector
from mysql.connector import Error
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'amin_furniture_secret_key_2025'

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

@app.route('/')
def index():
    conn = get_db_connection()
    if not conn:
        flash('Database connection failed!', 'error')
        return render_template('index.html', stats={})
    
    cursor = conn.cursor(dictionary=True)
    stats = {}
    
    try:
        cursor.execute("SELECT COUNT(*) as count FROM Products")
        stats['total_products'] = cursor.fetchone()['count']
        
        
        cursor.execute("SELECT COUNT(*) as count FROM Products WHERE StockQuantity < 10")
        stats['low_stock'] = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM Orders")
        stats['total_orders'] = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM Orders WHERE Status = 'Pending'")
        stats['pending_orders'] = cursor.fetchone()['count']
        
        
        cursor.execute("SELECT SUM(TotalAmount) as total FROM Orders WHERE Status = 'Completed'")
        result = cursor.fetchone()
        stats['total_revenue'] = result['total'] if result['total'] else 0
        
        cursor.execute("""
            SELECT o.OrderID, o.OrderDate, o.TotalAmount, o.Status,
                   c.FirstName, c.LastName
            FROM Orders o
            JOIN Customers c ON o.CustomerID = c.CustomerID
            ORDER BY o.OrderDate DESC
            LIMIT 5
        """)
        stats['recent_orders'] = cursor.fetchall()
        
    except Error as e:
        flash(f'Error fetching statistics: {e}', 'error')
    finally:
        cursor.close()
        conn.close()
    
    return render_template('index.html', stats=stats)

@app.route('/products')
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
                   c.CategoryName, s.SupplierName
            FROM Products p
            LEFT JOIN Categories c ON p.CategoryID = c.CategoryID
            LEFT JOIN Suppliers s ON p.SupplierID = s.SupplierID
            WHERE 1=1
        """
        params = []
        
        if search:
            query += " AND (p.ProductName LIKE %s OR p.Material LIKE %s)"
            params.extend([f'%{search}%', f'%{search}%'])
        
        if category:
            query += " AND c.CategoryID = %s"
            params.append(category)
        
        query += " ORDER BY p.ProductName"
        
        cursor.execute(query, params)
        products = cursor.fetchall()
        
        cursor.execute("SELECT CategoryID, CategoryName FROM Categories ORDER BY CategoryName")
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
                                   StockQuantity, CategoryID, SupplierID, DateAdded)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                request.form['product_name'],
                request.form['dimensions'],
                request.form['color'],
                request.form['material'],
                float(request.form['selling_price']),
                int(request.form['stock_quantity']),
                int(request.form['category_id']) if request.form['category_id'] else None,
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
        cursor.execute("SELECT CategoryID, CategoryName FROM Categories ORDER BY CategoryName")
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
                    SellingPrice = %s, StockQuantity = %s, CategoryID = %s, SupplierID = %s
                WHERE ProductID = %s
            """, (
                request.form['product_name'],
                request.form['dimensions'],
                request.form['color'],
                request.form['material'],
                float(request.form['selling_price']),
                int(request.form['stock_quantity']),
                int(request.form['category_id']) if request.form['category_id'] else None,
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
        
        cursor.execute("SELECT CategoryID, CategoryName FROM Categories ORDER BY CategoryName")
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

@app.route('/orders')
def orders():
    conn = get_db_connection()
    if not conn:
        flash('Database connection failed!', 'error')
        return render_template('orders.html', orders=[])
    
    cursor = conn.cursor(dictionary=True)
    status_filter = request.args.get('status', '')
    
    try:
        query = """
            SELECT o.OrderID, o.OrderDate, o.TotalAmount, o.Status,
                   c.FirstName, c.LastName, c.PhoneNumber,
                   e.FirstName as EmpFirstName, e.LastName as EmpLastName
            FROM Orders o
            JOIN Customers c ON o.CustomerID = c.CustomerID
            LEFT JOIN Employees e ON o.EmployeeID = e.EmployeeID
            WHERE 1=1
        """
        params = []
        
        if status_filter:
            query += " AND o.Status = %s"
            params.append(status_filter)
        
        query += " ORDER BY o.OrderDate DESC"
        
        cursor.execute(query, params)
        orders = cursor.fetchall()
        
    except Error as e:
        flash(f'Error fetching orders: {e}', 'error')
        orders = []
    finally:
        cursor.close()
        conn.close()
    
    return render_template('orders.html', orders=orders, status_filter=status_filter)

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
                   e.FirstName as EmpFirstName, e.LastName as EmpLastName
            FROM Orders o
            JOIN Customers c ON o.CustomerID = c.CustomerID
            LEFT JOIN Employees e ON o.EmployeeID = e.EmployeeID
            WHERE o.OrderID = %s
        """, (order_id,))
        order = cursor.fetchone()
        
        if not order:
            flash('Order not found!', 'error')
            return redirect(url_for('orders'))
        
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
def update_order_status(order_id):
    conn = get_db_connection()
    if not conn:
        flash('Database connection failed!', 'error')
        return redirect(url_for('orders'))
    
    cursor = conn.cursor()
    new_status = request.form.get('status')
    
    try:
        cursor.execute("""
            UPDATE Orders SET Status = %s WHERE OrderID = %s
        """, (new_status, order_id))
        conn.commit()
        flash(f'Order status updated to {new_status}!', 'success')
    except Error as e:
        flash(f'Error updating order status: {e}', 'error')
        conn.rollback()
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('order_details', order_id=order_id))

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
                   c.CategoryName, s.SupplierName,
                   CASE 
                       WHEN p.StockQuantity < 10 THEN 'Low'
                       WHEN p.StockQuantity < 20 THEN 'Medium'
                       ELSE 'Good'
                   END as StockStatus
            FROM Products p
            LEFT JOIN Categories c ON p.CategoryID = c.CategoryID
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
            SELECT c.CategoryName, SUM(op.Quantity * op.PricePerUnit) as TotalRevenue,
                   SUM(op.Quantity) as TotalItems
            FROM Order_Product op
            JOIN Products p ON op.ProductID = p.ProductID
            JOIN Categories c ON p.CategoryID = c.CategoryID
            JOIN Orders o ON op.OrderID = o.OrderID
            WHERE o.Status = 'Completed'
            GROUP BY c.CategoryID, c.CategoryName
            ORDER BY TotalRevenue DESC
        """)
        reports['sales_by_category'] = cursor.fetchall()
        
        cursor.execute("""
            SELECT e.FirstName, e.LastName, COUNT(o.OrderID) as OrderCount,
                   SUM(o.TotalAmount) as TotalSales
            FROM Employees e
            LEFT JOIN Orders o ON e.EmployeeID = o.EmployeeID
            WHERE e.Position = 'Sales Associate'
            GROUP BY e.EmployeeID, e.FirstName, e.LastName
            ORDER BY TotalSales DESC
        """)
        reports['employee_performance'] = cursor.fetchall()
        
        cursor.execute("""
            SELECT DATE_FORMAT(OrderDate, '%Y-%m') as Month,
                   COUNT(*) as OrderCount,
                   SUM(TotalAmount) as TotalSales
            FROM Orders
            WHERE Status = 'Completed'
            GROUP BY DATE_FORMAT(OrderDate, '%Y-%m')
            ORDER BY Month DESC
            LIMIT 6
        """)
        reports['monthly_sales'] = cursor.fetchall()
        
    except Error as e:
        flash(f'Error generating reports: {e}', 'error')
    finally:
        cursor.close()
        conn.close()
    
    return render_template('reports.html', reports=reports)

if __name__ == '__main__':
    print("\n AMIN Furniture Store - Database Management System")
    print(" Students: Malak Milhem, 1220031 - Layal Hajji, 1220871")
    print(" Starting Flask application...")
    print(" Access the application at: http://localhost:5000\n")
    app.run(debug=True, host='0.0.0.0', port=5000)

