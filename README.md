# 🪑 AMIN Furniture Store - Database Management System

A comprehensive web-based database management system for AMIN Furniture Store in Ramallah, Palestine. This system handles customer orders, product inventory, supplier management, employee information, and business analytics.

**Students:** Malak Milhem (1220031) & Layal Hajji (1220871)

---

## 📋 Features

### 👥 Multi-Role System
- **Customers**: Browse catalog, add to cart, place orders, view order history, cancel orders
- **Employees**: Manage products, view/update orders, handle customer information
- **Managers**: Full access + employee management, inventory control, sales reports & analytics

### 🛍️ Core Functionalities
- ✅ Product catalog with search and filtering
- ✅ Shopping cart and checkout system
- ✅ Order management with status tracking (Pending, Processing, Completed, Cancelled)
- ✅ Payment processing (Cash, Card, Bank Transfer, E-payment)
- ✅ Delivery tracking and management
- ✅ Customer and employee profiles
- ✅ Supplier management with product tracking
- ✅ Inventory monitoring with low stock alerts
- ✅ Sales reports and analytics (Manager only)
- ✅ Employee performance tracking (Manager only)

### 🔒 Security & Validation
- Role-based access control (RBAC)
- Input validation (names, phone numbers, dates, payment info)
- Secure session management
- Data integrity checks

---

## 🛠️ Technologies Used

- **Backend**: Python 3.x, Flask
- **Database**: MySQL
- **Frontend**: HTML, CSS, JavaScript
- **Libraries**: 
  - `mysql-connector-python` - Database connectivity
  - `Flask` - Web framework
  - `Lucide Icons` - Icon library
  - `Chart.js` - Data visualization (reports)

---

## 📦 Installation

### Prerequisites
- Python 3.7 or higher
- MySQL Server
- pip (Python package manager)

### Setup Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/MalakM15/Furniture-Store-Database.git
   cd Furniture-Store-Database/phase3/phase3
   ```

2. **Create and configure the database**
   ```bash
   # Using MySQL Command Line
   mysql -u root -p < 1220031_1220871.sql
   
   # OR using MySQL Workbench
   # Import the 1220031_1220871.sql file
   ```

3. **Configure database connection**
   
   Open `1220031_1220871.py` and update the `DB_CONFIG` dictionary:
   ```python
   DB_CONFIG = {
       'host': 'localhost',
       'database': 'amin_furniture',
       'user': 'root',           # Your MySQL username
       'password': 'your_password'  # Your MySQL password
   }
   ```

4. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Run the application**
   ```bash
   python 1220031_1220871.py
   ```

6. **Access the application**
   
   Open your web browser and navigate to:
   ```
   http://localhost:5000
   ```

---

## 🗄️ Database Schema

The database consists of **12 entities**:

1. **Products** - Furniture items with details (dimensions, color, material, price)
2. **Categories** - Product classifications (Bedroom, Living Room, Office, etc.)
3. **Suppliers** - Supplier information and contacts
4. **Customers** - Customer profiles and contact information
5. **Employees** - Staff information (Manager, Sales Associate, Delivery Staff)
6. **Orders** - Customer purchase transactions
7. **Order_Product** - Order items (many-to-many relationship)
8. **Payments** - Payment records for orders
9. **Delivery** - Delivery information and tracking
10. **Delivery_Employee** - Employee-delivery assignments (many-to-many)
11. **Purchases** - Store purchases from suppliers
12. **Purchase_Product** - Purchase items

**Database normalization:** 3NF (Third Normal Form)

---

## 🔐 Default Login Credentials

### Customer Account
- **Email**: Any customer email from the database (e.g., `ahmad.salem@email.com`)
- **Role**: Customer

### Employee Account
- **Email**: Any Employee email from the database (e.g.,`layla@aminfurniture.ps`)
- **Role**: Employee

### Manager Account
- **Email**: Any Manager email from the database (e.g.,`khalil@aminfurniture.ps`)
- **Role**: Manager

---

## 📁 Project Structure

```
phase3/
├── 1220031_1220871.py          # Main Flask application
├── 1220031_1220871.sql          # Database schema and sample data
├── requirements.txt              # Python dependencies
├── README.md                    # This file
└── templates/                   # HTML templates
    ├── base.html                # Base layout template
    ├── index.html               # Home page
    ├── login.html               # Login page
    ├── register.html            # Customer registration
    ├── products.html            # Product listing
    ├── orders.html              # Order management
    ├── customers.html           # Customer management
    ├── suppliers.html           # Supplier management
    ├── employees.html           # Employee management (Manager)
    ├── inventory.html           # Inventory management
    ├── reports.html             # Business reports (Manager)
    ├── customer/                # Customer-specific pages
    │   ├── dashboard.html
    │   ├── catalog.html
    │   ├── cart.html
    │   ├── checkout.html
    │   ├── orders.html
    │   ├── order_details.html
    │   └── profile.html
    └── employee/                # Employee/Manager pages
        ├── dashboard.html
        └── profile.html
```

---

## 🎯 Key Features Explained

### Order Management
- Customers can place orders with delivery address and payment method
- Employees/Managers can view, update status, and assign orders
- Automatic stock deduction upon order placement
- Stock restoration when orders are cancelled

### Payment Processing
- Multiple payment methods (Card, Bank Transfer, E-payment)
- Validated payment information (card numbers, expiry dates, CVV)
- Payment amount automatically matches order total

### Inventory Management
- Real-time stock tracking
- Low stock alerts (< 10 units)
- Inventory value calculation
- Stock updates on order/cancellation

### Reports & Analytics (Manager Only)
- Top selling products
- Sales by category
- Employee performance metrics
- Monthly sales trends

---

## 📝 Notes

- The database includes sample data for testing
- All dates should be in `YYYY-MM-DD` format
- Phone numbers should contain only digits
- Names must contain only letters and spaces

---

## 👨‍💻 Developers

- **Malak Milhem**
- **Layal Hajji** 

---

## 📄 License

This project is part of a Database Systems course assignment.

---

## 🐛 Troubleshooting

### Database Connection Error
- Verify MySQL is running
- Check database credentials in `DB_CONFIG`
- Ensure `amin_furniture` database exists

### Module Not Found Error
- Run `pip install -r requirements.txt`
- Verify Python version (3.7+)

### Port Already in Use
- Change the port in the last line of `1220031_1220871.py`:
  ```python
  app.run(host='0.0.0.0', port=5000, debug=True)
  ```

---
