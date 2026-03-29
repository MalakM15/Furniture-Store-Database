# 🪑 AMIN Furniture Store - Database Management System

A comprehensive web-based database management system for AMIN Furniture Store in Ramallah, Palestine. This system handles customer orders, product inventory, supplier management, employee information, and business analytics.

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

| Role | Example Email | Access Level |
| :--- | :--- | :--- |
| **Customer** | `ahmad.salem@email.com` | Browse catalog, Manage Cart, Place/Cancel Orders |
| **Employee** | `layla@aminfurniture.ps` | Update Order Status, Manage Products, Customer Info |
| **Manager** | `khalil@aminfurniture.ps` | Full System Access, Sales Analytics, HR Management |

---

## 📁 Project Structure

```
phase3/
├── 1220031_1220871.py          # Main Flask application
├── 1220031_1220871.sql          # Database schema and sample data
├── templates/                   # HTML templates
├── requirements.txt              # Python dependencies
└── SETUP_INSTRUCTIONS.txt                   
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

- **Malak Milhem** & **Layal Hajji** 

---
