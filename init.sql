CREATE DATABASE IF NOT EXISTS personal_finance;
USE personal_finance;

-- 1. Accounts Table (Manages joint and individual accounts for you and your partner)
CREATE TABLE IF NOT EXISTS accounts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_account_name VARCHAR(150) NOT NULL UNIQUE,
    nickname VARCHAR(50) NOT NULL,
    account_type ENUM('Everyday', 'Savings', 'Credit Card', 'Investment') DEFAULT 'Everyday',
    institution_name VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    date_added DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Expense Categories Table (Normalized category dimension)
CREATE TABLE IF NOT EXISTS categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT
);

-- 3. Common Merchant Rules / Lookup Table (Learned AI categorizations & rules)
CREATE TABLE IF NOT EXISTS common_merchants (
    id INT AUTO_INCREMENT PRIMARY KEY,
    raw_pattern VARCHAR(255) NOT NULL UNIQUE,
    clean_merchant_name VARCHAR(150) NOT NULL,
    category_id INT NOT NULL,
    default_impulse_score INT DEFAULT 5,
    is_subscription BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (category_id) REFERENCES categories(id)
);

-- 4. Upload Logs Table (Staging & Audit Trail to prevent duplicate file processing)
CREATE TABLE IF NOT EXISTS upload_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    file_name VARCHAR(255) NOT NULL UNIQUE,
    file_content LONGBLOB,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    account_id INT NOT NULL,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (account_id) REFERENCES accounts(id)
);

-- 5. Fact Transactions Table (Core normalized transaction log with hash deduplication)
CREATE TABLE IF NOT EXISTS fact_transactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tx_hash VARCHAR(64) UNIQUE NOT NULL,       -- Cryptographic hash to block duplicate imports
    txn_date DATE NOT NULL,
    raw_description TEXT NOT NULL,             -- Raw string straight from the bank CSV
    amount DECIMAL(10, 2) NOT NULL,            -- Negative for expenses, positive for income/transfers
    account_id INT NOT NULL,
    common_merchant_id INT DEFAULT NULL,       -- Links to common_merchants if matched
    category_id INT DEFAULT NULL,              -- Direct category fallback if merchant is unmapped
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (account_id) REFERENCES accounts(id),
    FOREIGN KEY (common_merchant_id) REFERENCES common_merchants(id),
    FOREIGN KEY (category_id) REFERENCES categories(id)
);

-- Default Starter Categories
INSERT IGNORE INTO categories (category_name, description) VALUES 
('Groceries', 'Supermarket, fresh food, and daily essentials'),
('Dining & Takeaway', 'Restaurants, cafes, delivery services'),
('Utilities', 'Electricity, gas, water, internet, phone bills'),
('Transport', 'Public transit, fuel, rideshare, toll charges'),
('Entertainment', 'Movies, games, events, leisure activities'),
('Transfer', 'Internal movement of funds between accounts');

-- Default Starter Accounts (Customize names as needed for you and your partner)
INSERT IGNORE INTO accounts (full_account_name, nickname, account_type, institution_name, date_added) VALUES 
('Joint Everyday Account', 'Joint Everyday', 'Everyday', 'Bank A', CURDATE()),
('Joint Savings Account', 'Joint Savings', 'Savings', 'Bank A', CURDATE()),
('Sahaj Personal Card', 'Sahaj CC', 'Credit Card', 'Bank B', CURDATE()),
('Partner Personal Card', 'Partner CC', 'Credit Card', 'Bank C', CURDATE());