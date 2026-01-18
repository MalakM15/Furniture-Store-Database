-- AMIN Furniture Store Database Schema

-- Create database if it doesn't exist
CREATE DATABASE IF NOT EXISTS amin_furniture;

USE amin_furniture;

-- DROP TABLES IF EXISTS
DROP TABLE IF EXISTS Delivery, Payments, Order_Product, Purchase_Product, Orders, Purchases, Products, Employees, Customers, Suppliers;

-- CREATE TABLES


CREATE TABLE Suppliers (
    SupplierID INT PRIMARY KEY AUTO_INCREMENT,
    SupplierName VARCHAR(100) NOT NULL,
    ContactPerson VARCHAR(100),
    PhoneNumber VARCHAR(20),
    Email VARCHAR(100)
);

CREATE TABLE Products (
    ProductID INT PRIMARY KEY AUTO_INCREMENT,
    ProductName VARCHAR(200) NOT NULL,
    Dimensions VARCHAR(100),
    Color VARCHAR(50),
    Material VARCHAR(100),
    SellingPrice DECIMAL(10, 2) NOT NULL,
    StockQuantity INT DEFAULT 0,
    CategoryName VARCHAR(100),
    SupplierID INT,
    DateAdded DATE,
    FOREIGN KEY (SupplierID) REFERENCES Suppliers(SupplierID) ON DELETE SET NULL
);

CREATE TABLE Customers (
    CustomerID INT PRIMARY KEY AUTO_INCREMENT,
    FirstName VARCHAR(50) NOT NULL,
    LastName VARCHAR(50) NOT NULL,
    Email VARCHAR(100) UNIQUE,
    PhoneNumber VARCHAR(20),
    Address TEXT,
    RegistrationDate DATE,
    Password VARCHAR(255) NOT NULL
);

CREATE TABLE Employees (
    EmployeeID INT PRIMARY KEY AUTO_INCREMENT,
    FirstName VARCHAR(50) NOT NULL,
    LastName VARCHAR(50) NOT NULL,
    Position VARCHAR(50),
    HireDate DATE,
    Salary DECIMAL(10, 2),
    PhoneNumber VARCHAR(20),
    Email VARCHAR(100) UNIQUE,
    Password VARCHAR(255) NOT NULL
);

CREATE TABLE Orders (
    OrderID INT PRIMARY KEY AUTO_INCREMENT,
    CustomerID INT,
    EmployeeID INT,
    OrderDate DATE NOT NULL,
    Status VARCHAR(50) DEFAULT 'Pending',
    FOREIGN KEY (CustomerID) REFERENCES Customers(CustomerID) ON DELETE SET NULL,
    FOREIGN KEY (EmployeeID) REFERENCES Employees(EmployeeID) ON DELETE SET NULL
);

CREATE TABLE Order_Product (
    OrderDetailID INT PRIMARY KEY AUTO_INCREMENT,
    OrderID INT,
    ProductID INT,
    Quantity INT NOT NULL,
    PricePerUnit DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (OrderID) REFERENCES Orders(OrderID) ON DELETE CASCADE,
    FOREIGN KEY (ProductID) REFERENCES Products(ProductID) ON DELETE CASCADE
);


CREATE TABLE Purchases (
    PurchaseID INT PRIMARY KEY AUTO_INCREMENT,
    SupplierID INT,
    PurchaseDate DATE NOT NULL,
    TotalCost DECIMAL(10, 2) NOT NULL,
    ReceivedBy INT,
    FOREIGN KEY (SupplierID) REFERENCES Suppliers(SupplierID) ON DELETE SET NULL,
    FOREIGN KEY (ReceivedBy) REFERENCES Employees(EmployeeID) ON DELETE SET NULL
);


CREATE TABLE Purchase_Product (
    PurchaseDetailID INT PRIMARY KEY AUTO_INCREMENT,
    PurchaseID INT,
    ProductID INT,
    QuantityPurchased INT NOT NULL,
    CostPerUnit DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (PurchaseID) REFERENCES Purchases(PurchaseID) ON DELETE CASCADE,
    FOREIGN KEY (ProductID) REFERENCES Products(ProductID) ON DELETE CASCADE
);

CREATE TABLE Payments (
    PaymentID INT PRIMARY KEY AUTO_INCREMENT,
    OrderID INT,
    PaymentDate DATE NOT NULL,
    AmountPaid DECIMAL(10, 2) NOT NULL,
    PaymentMethod VARCHAR(50) NOT NULL,
    FOREIGN KEY (OrderID) REFERENCES Orders(OrderID) ON DELETE CASCADE
);

CREATE TABLE Delivery (
    OrderID INT PRIMARY KEY,
    EmployeeID INT,
    DeliveryAddress TEXT,
    ScheduledDate DATE,
    DeliveryDate DATE,
    FOREIGN KEY (OrderID) REFERENCES Orders(OrderID) ON DELETE CASCADE,
    FOREIGN KEY (EmployeeID) REFERENCES Employees(EmployeeID) ON DELETE SET NULL
);

--  DUMMY DATA

INSERT INTO Suppliers (SupplierName, ContactPerson, PhoneNumber, Email) VALUES
('Palestine Furniture Co.', 'Ahmed Mansour', '0599123456', 'ahmed@palestinefurniture.ps'),
('Modern Home Supplies', 'Sara Khoury', '0599234567', 'sara@modernhome.ps'),
('Office Solutions Ltd.', 'Mohammad Ali', '0599345678', 'mohammad@officesolutions.ps'),
('Luxury Interiors', 'Fatima Nasser', '0599456789', 'fatima@luxuryinteriors.ps'),
('Budget Furniture', 'Omar Saleh', '0599567890', 'omar@budgetfurniture.ps');

INSERT INTO Employees (FirstName, LastName, Position, HireDate, Salary, PhoneNumber, Email, Password) VALUES
('Khalil', 'Abu Hamad', 'Manager', '2020-01-15', 5000.00, '0599111111', 'khalil@aminfurniture.ps', '1234'),
('Layla', 'Mahmoud', 'Sales Associate', '2021-03-20', 2500.00, '0599222222', 'layla@aminfurniture.ps', '1234'),
('Youssef', 'Ibrahim', 'Sales Associate', '2021-05-10', 2500.00, '0599333333', 'youssef@aminfurniture.ps', '1234'),
('Hassan', 'Hassan', 'Delivery Staff', '2022-01-08', 2000.00, '0599444444', 'hassan@aminfurniture.ps', '1234'),
('Rami', 'Said', 'Delivery Staff', '2022-02-15', 2000.00, '0599555555', 'rami@aminfurniture.ps', '1234'),
('Hala', 'Omar', 'Warehouse Manager', '2020-06-01', 3500.00, '0599666666', 'hala@aminfurniture.ps', '1234');

INSERT INTO Products (ProductName, Dimensions, Color, Material, SellingPrice, StockQuantity, CategoryName, SupplierID, DateAdded) VALUES
('Bed', '200x200 cm', 'Brown', 'Wood', 1500.00, 8, 'Bedroom', 1, '2023-01-10'),
('Bedroom Set', '320x280 cm', 'Walnut', 'Wood', 5200.00, 4, 'Bedroom', 1, '2023-01-10'),
('Wardrobe', '180x220 cm', 'Brown', 'MDF', 2000.00, 5, 'Bedroom', 2, '2023-02-15'),
('Nightstand', '50x40 cm', 'Brown', 'Wood', 300.00, 20, 'Bedroom', 1, '2023-01-10'),
('Leather Sofa', '220x90 cm', 'Black', 'Leather', 3500.00, 6, 'Living Room', 3, '2023-03-01'),
('Coffee Table', '120x60 cm', 'Brown', 'Glass & Wood', 800.00, 15, 'Living Room', 2, '2023-03-01'),
('TV Stand', '180x45 cm', 'Walnut', 'MDF', 1200.00, 10, 'Living Room', 2, '2023-03-15'),
('Office Desk', '160x80 cm', 'White', 'MDF', 1500.00, 8, 'Office', 4, '2023-04-01'),
('Drawer', '45x50 cm', 'White', 'Wood', 700.00, 12, 'Office', 4, '2023-04-10'),
('Dining Table', '180x90 cm', 'Brown', 'Wood', 2500.00, 7, 'Dining Room', 1, '2023-05-01'),
('Dining Chairs', '45x45 cm', 'Beige', 'Wood & Fabric', 1800.00, 6, 'Dining Room', 1, '2023-05-01'),
('Sofa', '210x95 cm', 'Beige', 'Fabric', 2800.00, 6, 'Living Room', 3, '2023-05-20'),
('Outdoor Setting', '300x120 cm', 'Gray', 'Metal & Rattan', 4000.00, 3, 'Outdoor', 5, '2023-06-10'),
('Outdoor Swing', '120x110 cm', 'Gray', 'Metal', 2200.00, 5, 'Outdoor', 5, '2023-06-15'),
('Single Bed', '90x200 cm', 'White', 'Wood', 800.00, 18, 'Bedroom', 5, '2023-06-01'),
('Wardrobe Brown', '200x230 cm', 'Brown', 'Wood', 2600.00, 3, 'Bedroom', 2, '2023-06-12');

INSERT INTO Customers (FirstName, LastName, Email, PhoneNumber, Address, RegistrationDate, Password) VALUES
('Ahmad', 'Salem', 'ahmad.salem@email.com', '0599111222', 'Ramallah, Al-Bireh Street', '2023-01-05', '1234'),
('Mariam', 'Khalil', 'mariam.khalil@email.com', '0599222333', 'Ramallah, Al-Manara Square', '2023-01-10', '1234'),
('Omar', 'Nasser', 'omar.nasser@email.com', '0599333444', 'Ramallah, Al-Irsal Street', '2023-02-01', '1234'),
('Lina', 'Mahmoud', 'lina.mahmoud@email.com', '0599444555', 'Ramallah, Al-Masyoun', '2023-02-15', '1234'),
('Khaled', 'Ibrahim', 'khaled.ibrahim@email.com', '0599555666', 'Ramallah, Al-Tireh', '2023-03-01', '1234'),
('Rana', 'Hassan', 'rana.hassan@email.com', '0599666777', 'Ramallah, Al-Balou', '2023-03-10', '1234'),
('Tamer', 'Said', 'tamer.said@email.com', '0599777888', 'Ramallah, Al-Jalazoun', '2023-04-01', '1234'),
('Dina', 'Omar', 'dina.omar@email.com', '0599888999', 'Ramallah, Al-Masyoun', '2023-04-15', '1234');


INSERT INTO Orders (CustomerID, EmployeeID, OrderDate, Status) VALUES
(1, 2, '2023-02-12', 'Completed'),
(2, 2, '2023-06-05', 'Completed'),
(3, 3, '2023-11-22', 'Completed'),
(4, 2, '2024-03-18', 'Completed'),
(5, 3, '2024-08-09', 'Completed'),
(6, 2, '2024-12-27', 'Completed'),
(7, 3, '2025-05-14', 'Completed'),
(8, 2, '2025-10-03', 'Ready to Deliver'),
(1, 3, '2025-12-21', 'Processing'),
(2, 2, '2026-01-08', 'Pending'),
(3, 2, '2026-03-12', 'Scheduled for Delivery'),
(4, 3, '2026-06-19', 'Ready to Deliver');


INSERT INTO Order_Product (OrderID, ProductID, Quantity, PricePerUnit) VALUES
(1, 1, 1, 1500.00),
(2, 5, 1, 3500.00),
(3, 14, 1, 5000.00),
(4, 11, 1, 2500.00),
(5, 8, 1, 1500.00),
(6, 14, 1, 5000.00),
(6, 13, 1, 3000.00),
(7, 8, 1, 1500.00),
(8, 13, 1, 3000.00),
(9, 2, 1, 1200.00),
(10, 12, 1, 1800.00),
(11, 3, 1, 2000.00),
(12, 6, 1, 800.00),
(12, 7, 1, 700.00);


INSERT INTO Purchases (SupplierID, PurchaseDate, TotalCost, ReceivedBy) VALUES
(1, '2023-01-10', 10000.00, 6),
(2, '2023-02-15', 15000.00, 6),
(3, '2023-03-01', 20000.00, 6),
(2, '2023-03-15', 12000.00, 6),
(4, '2023-04-01', 25000.00, 6),
(4, '2023-04-10', 9600.00, 6),
(1, '2023-05-01', 30000.00, 6),
(2, '2023-05-15', 21000.00, 6),
(5, '2023-06-01', 14400.00, 6);


INSERT INTO Purchase_Product (PurchaseID, ProductID, QuantityPurchased, CostPerUnit) VALUES
(1, 1, 10, 1000.00),
(1, 2, 15, 800.00),
(2, 3, 8, 1500.00),
(2, 6, 20, 500.00),
(3, 5, 10, 2500.00),
(4, 7, 15, 800.00),
(5, 8, 12, 1000.00),
(5, 9, 20, 800.00),
(6, 10, 15, 640.00),
(7, 11, 10, 2000.00),
(7, 12, 5, 1500.00),
(8, 13, 5, 2500.00),
(8, 14, 3, 4000.00),
(9, 15, 20, 720.00);


INSERT INTO Payments (OrderID, PaymentDate, AmountPaid, PaymentMethod) VALUES
(1, '2023-06-10', 1500.00, 'Card'),
(2, '2023-06-15', 3500.00, 'Card'),
(3, '2023-06-20', 3000.00, 'Bank Transfer'),
(3, '2023-06-21', 2000.00, 'Bank Transfer'),
(4, '2023-07-01', 2500.00, 'Card'),
(5, '2023-07-05', 1200.00, 'Card'),
(6, '2023-07-10', 5000.00, 'Bank Transfer'),
(6, '2023-07-11', 3000.00, 'Bank Transfer'),
(7, '2023-07-15', 1500.00, 'Card'),
(8, '2023-07-20', 1500.00, 'E-payment'),
(8, '2023-07-21', 1500.00, 'E-payment');


INSERT INTO Delivery (OrderID, EmployeeID, DeliveryAddress, ScheduledDate, DeliveryDate) VALUES
(1, 4, 'Ramallah, Al-Bireh Street', '2023-06-12', '2023-06-12'),
(2, 4, 'Ramallah, Al-Manara Square', '2023-06-17', '2023-06-17'),
(3, 5, 'Ramallah, Al-Irsal Street', '2023-06-22', '2023-06-22'),
(4, 4, 'Ramallah, Al-Masyoun', '2023-07-03', '2023-07-03'),
(5, 5, 'Ramallah, Al-Tireh', '2023-07-07', '2023-07-07'),
(6, 4, 'Ramallah, Al-Balou', '2023-07-12', '2023-07-12'),
(7, 5, 'Ramallah, Al-Jalazoun', '2023-07-17', '2023-07-17'),
(8, NULL, 'Ramallah, Al-Masyoun', '2023-11-22', NULL),
(9, NULL, 'Ramallah, Al-Bireh Street', NULL, NULL),
(10, NULL, 'Ramallah, Al-Manara Square', NULL, NULL),
(11, 5, 'Ramallah, Al-Irsal Street', '2023-11-30', NULL),
(12, NULL, 'Ramallah, Al-Masyoun', NULL, NULL);
