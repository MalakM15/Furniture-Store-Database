-- AMIN Furniture Store Database Schema

-- Create database if it doesn't exist
CREATE DATABASE IF NOT EXISTS amin_furniture;

USE amin_furniture;

-- CREATE TABLES


CREATE TABLE Categories (
    CategoryID INT PRIMARY KEY AUTO_INCREMENT,
    CategoryName VARCHAR(100) NOT NULL,
    Description TEXT
);

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
    CategoryID INT,
    SupplierID INT,
    DateAdded DATE,
    FOREIGN KEY (CategoryID) REFERENCES Categories(CategoryID) ON DELETE SET NULL,
    FOREIGN KEY (SupplierID) REFERENCES Suppliers(SupplierID) ON DELETE SET NULL
);

CREATE TABLE Customers (
    CustomerID INT PRIMARY KEY AUTO_INCREMENT,
    FirstName VARCHAR(50) NOT NULL,
    LastName VARCHAR(50) NOT NULL,
    Email VARCHAR(100),
    PhoneNumber VARCHAR(20),
    Address TEXT,
    RegistrationDate DATE
);

CREATE TABLE Employees (
    EmployeeID INT PRIMARY KEY AUTO_INCREMENT,
    FirstName VARCHAR(50) NOT NULL,
    LastName VARCHAR(50) NOT NULL,
    Position VARCHAR(50),
    HireDate DATE,
    Salary DECIMAL(10, 2),
    PhoneNumber VARCHAR(20),
    Email VARCHAR(100)
);

CREATE TABLE Orders (
    OrderID INT PRIMARY KEY AUTO_INCREMENT,
    CustomerID INT,
    EmployeeID INT,
    OrderDate DATE NOT NULL,
    TotalAmount DECIMAL(10, 2) NOT NULL,
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
    DeliveryID INT PRIMARY KEY AUTO_INCREMENT,
    OrderID INT UNIQUE,
    EmployeeID INT,
    DeliveryAddress TEXT,
    ScheduledDate DATE,
    DeliveryDate DATE,
    Status VARCHAR(50) DEFAULT 'Scheduled',
    FOREIGN KEY (OrderID) REFERENCES Orders(OrderID) ON DELETE CASCADE,
    FOREIGN KEY (EmployeeID) REFERENCES Employees(EmployeeID) ON DELETE SET NULL
);

CREATE TABLE Delivery_Employee (
    DeliveryEmployeeID INT PRIMARY KEY AUTO_INCREMENT,
    DeliveryID INT,
    EmployeeID INT,
    FOREIGN KEY (DeliveryID) REFERENCES Delivery(DeliveryID) ON DELETE CASCADE,
    FOREIGN KEY (EmployeeID) REFERENCES Employees(EmployeeID) ON DELETE CASCADE
);

--  DUMMY DATA

INSERT INTO Categories (CategoryName, Description) VALUES
('Bedroom', 'Furniture for bedrooms including beds, wardrobes, and nightstands'),
('Living Room', 'Sofas, coffee tables, TV stands, and living room accessories'),
('Office', 'Desks, office chairs, filing cabinets, and office equipment'),
('Dining Room', 'Dining tables, chairs, and dining room furniture'),
('Kitchen', 'Kitchen cabinets, islands, and storage solutions');


INSERT INTO Suppliers (SupplierName, ContactPerson, PhoneNumber, Email) VALUES
('Palestine Furniture Co.', 'Ahmed Mansour', '0599123456', 'ahmed@palestinefurniture.ps'),
('Modern Home Supplies', 'Sara Khoury', '0599234567', 'sara@modernhome.ps'),
('Office Solutions Ltd.', 'Mohammad Ali', '0599345678', 'mohammad@officesolutions.ps'),
('Luxury Interiors', 'Fatima Nasser', '0599456789', 'fatima@luxuryinteriors.ps'),
('Budget Furniture', 'Omar Saleh', '0599567890', 'omar@budgetfurniture.ps');

INSERT INTO Employees (FirstName, LastName, Position, HireDate, Salary, PhoneNumber, Email) VALUES
('Khalil', 'Abu Hamad', 'Manager', '2020-01-15', 5000.00, '0599111111', 'khalil@aminfurniture.ps'),
('Layla', 'Mahmoud', 'Sales Associate', '2021-03-20', 2500.00, '0599222222', 'layla@aminfurniture.ps'),
('Youssef', 'Ibrahim', 'Sales Associate', '2021-05-10', 2500.00, '0599333333', 'youssef@aminfurniture.ps'),
('Nour', 'Hassan', 'Delivery Staff', '2022-01-08', 2000.00, '0599444444', 'nour@aminfurniture.ps'),
('Rami', 'Said', 'Delivery Staff', '2022-02-15', 2000.00, '0599555555', 'rami@aminfurniture.ps'),
('Hala', 'Omar', 'Warehouse Manager', '2020-06-01', 3500.00, '0599666666', 'hala@aminfurniture.ps');

INSERT INTO Products (ProductName, Dimensions, Color, Material, SellingPrice, StockQuantity, CategoryID, SupplierID, DateAdded) VALUES
('King Size Bed Frame', '200x200 cm', 'Brown', 'Wood', 1500.00, 8, 1, 1, '2023-01-10'),
('Queen Size Bed Frame', '160x200 cm', 'White', 'Wood', 1200.00, 12, 1, 1, '2023-01-10'),
('Wardrobe 3 Doors', '180x220 cm', 'Brown', 'MDF', 2000.00, 5, 1, 2, '2023-02-15'),
('Nightstand', '50x40 cm', 'Brown', 'Wood', 300.00, 20, 1, 1, '2023-01-10'),
('Leather Sofa 3 Seater', '220x90 cm', 'Black', 'Leather', 3500.00, 6, 2, 3, '2023-03-01'),
('Coffee Table', '120x60 cm', 'Brown', 'Glass & Wood', 800.00, 15, 2, 2, '2023-03-01'),
('TV Stand', '180x45 cm', 'Black', 'MDF', 1200.00, 10, 2, 2, '2023-03-15'),
('Office Desk', '160x80 cm', 'White', 'MDF', 1500.00, 8, 3, 4, '2023-04-01'),
('Ergonomic Office Chair', '60x60 cm', 'Black', 'Mesh & Metal', 1200.00, 15, 3, 4, '2023-04-01'),
('Filing Cabinet 4 Drawers', '45x50 cm', 'Gray', 'Metal', 800.00, 12, 3, 4, '2023-04-10'),
('Dining Table 6 Seater', '180x90 cm', 'Brown', 'Wood', 2500.00, 7, 4, 1, '2023-05-01'),
('Dining Chairs Set (6)', '45x45 cm', 'Brown', 'Wood & Fabric', 1800.00, 4, 4, 1, '2023-05-01'),
('Kitchen Island', '120x80 cm', 'White', 'MDF', 3000.00, 3, 5, 2, '2023-05-15'),
('Kitchen Cabinet Set', '300x90 cm', 'White', 'MDF', 5000.00, 2, 5, 2, '2023-05-15'),
('Single Bed Frame', '90x200 cm', 'White', 'Wood', 800.00, 18, 1, 5, '2023-06-01');

INSERT INTO Customers (FirstName, LastName, Email, PhoneNumber, Address, RegistrationDate) VALUES
('Ahmad', 'Salem', 'ahmad.salem@email.com', '0599111222', 'Ramallah, Al-Bireh Street', '2023-01-05'),
('Mariam', 'Khalil', 'mariam.khalil@email.com', '0599222333', 'Ramallah, Al-Manara Square', '2023-01-10'),
('Omar', 'Nasser', 'omar.nasser@email.com', '0599333444', 'Ramallah, Al-Irsal Street', '2023-02-01'),
('Lina', 'Mahmoud', 'lina.mahmoud@email.com', '0599444555', 'Ramallah, Al-Masyoun', '2023-02-15'),
('Khaled', 'Ibrahim', 'khaled.ibrahim@email.com', '0599555666', 'Ramallah, Al-Tireh', '2023-03-01'),
('Rana', 'Hassan', 'rana.hassan@email.com', '0599666777', 'Ramallah, Al-Balou', '2023-03-10'),
('Tamer', 'Said', 'tamer.said@email.com', '0599777888', 'Ramallah, Al-Jalazoun', '2023-04-01'),
('Dina', 'Omar', 'dina.omar@email.com', '0599888999', 'Ramallah, Al-Masyoun', '2023-04-15');


INSERT INTO Orders (CustomerID, EmployeeID, OrderDate, TotalAmount, Status) VALUES
(1, 2, '2025-06-10', 1500.00, 'Completed'),
(2, 2, '2025-06-15', 3500.00, 'Completed'),
(3, 3, '2025-06-20', 5000.00, 'Completed'),
(4, 2, '2025-07-01', 2500.00, 'Completed'),
(5, 3, '2025-07-05', 1200.00, 'Completed'),
(6, 2, '2025-07-10', 8000.00, 'Completed'),
(7, 3, '2025-07-15', 1500.00, 'Completed'),
(8, 2, '2025-11-20', 3000.00, 'Pending'),
(1, 3, '2025-11-25', 1200.00, 'Pending'),
(2, 2, '2025-11-01', 1800.00, 'Pending');


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
(10, 12, 1, 1800.00);


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
(1, '2023-06-10', 1500.00, 'Cash'),
(2, '2023-06-15', 3500.00, 'Card'),
(3, '2023-06-20', 3000.00, 'Bank Transfer'),
(3, '2023-06-21', 2000.00, 'Bank Transfer'),
(4, '2023-07-01', 2500.00, 'Card'),
(5, '2023-07-05', 1200.00, 'Cash'),
(6, '2023-07-10', 5000.00, 'Bank Transfer'),
(6, '2023-07-11', 3000.00, 'Bank Transfer'),
(7, '2023-07-15', 1500.00, 'Card'),
(8, '2023-07-20', 1500.00, 'E-payment'),
(8, '2023-07-21', 1500.00, 'E-payment');


INSERT INTO Delivery (OrderID, EmployeeID, DeliveryAddress, ScheduledDate, DeliveryDate, Status) VALUES
(1, 4, 'Ramallah, Al-Bireh Street', '2023-06-12', '2023-06-12', 'Delivered'),
(2, 4, 'Ramallah, Al-Manara Square', '2023-06-17', '2023-06-17', 'Delivered'),
(3, 5, 'Ramallah, Al-Irsal Street', '2023-06-22', '2023-06-22', 'Delivered'),
(4, 4, 'Ramallah, Al-Masyoun', '2023-07-03', '2023-07-03', 'Delivered'),
(5, 5, 'Ramallah, Al-Tireh', '2023-07-07', '2023-07-07', 'Delivered'),
(6, 4, 'Ramallah, Al-Balou', '2023-07-12', '2023-07-12', 'Delivered'),
(7, 5, 'Ramallah, Al-Jalazoun', '2023-07-17', '2023-07-17', 'Delivered'),
(8, 4, 'Ramallah, Al-Masyoun', '2023-07-22', NULL, 'Scheduled'),
(9, 5, 'Ramallah, Al-Bireh Street', '2023-07-27', NULL, 'Scheduled'),
(10, 4, 'Ramallah, Al-Manara Square', '2023-08-03', NULL, 'Scheduled');


INSERT INTO Delivery_Employee (DeliveryID, EmployeeID) VALUES
(1, 4),
(2, 4),
(3, 5),
(4, 4),
(5, 5),
(6, 4),
(6, 5),
(7, 5),
(8, 4),
(9, 5),
(10, 4);
