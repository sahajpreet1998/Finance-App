# src/db_manager.py
import mysql.connector
from mysql.connector import Error
import pandas as pd
from config import DB_CONFIG, logger

def get_connection():
    """Establish a connection to the MySQL database using central DB_CONFIG."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        if conn.is_connected():
            return conn
    except Error as e:
        logger.error(f"Error while connecting to MySQL: {e}")
        return None
    return None

def test_connection():
    """Test the database connection and log success/failure."""
    conn = get_connection()
    if conn and conn.is_connected():
        logger.info("Database connection test successful!")
        conn.close()
        return True
    else:
        logger.error("Database connection test failed.")
        return False

# ===================================================================
# ACCOUNTS MANAGEMENT
# ===================================================================
def save_account(full_account_name, nickname, account_type, institution_name, date_added):
    conn = get_connection()
    if not conn: return False
    cursor = conn.cursor()
    try:
        cursor.execute(
            """INSERT INTO accounts (full_account_name, nickname, account_type, institution_name, date_added)
               VALUES (%s, %s, %s, %s, %s)""",
            (full_account_name, nickname, account_type, institution_name, date_added)
        )
        conn.commit()
        return True
    except Error as e:
        print(f"Error saving account: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def get_accounts_dataframe():
    conn = get_connection()
    if not conn: return pd.DataFrame()
    try:
        return pd.read_sql("SELECT * FROM accounts", conn)
    finally:
        conn.close()

def get_all_accounts():
    """Fetches active accounts for UI dropdown selection during CSV uploads."""
    conn = get_connection()
    if not conn: return []
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id, full_account_name, nickname FROM accounts WHERE is_active = TRUE")
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

def update_account(account_id, full_account_name, nickname, institution_name, account_type):
    conn = get_connection()
    if not conn: return False
    cursor = conn.cursor()
    try:
        cursor.execute(
            """UPDATE accounts SET full_account_name=%s, nickname=%s, institution_name=%s, account_type=%s WHERE id=%s""",
            (full_account_name, nickname, institution_name, account_type, account_id)
        )
        conn.commit()
        return True
    finally:
        cursor.close()
        conn.close()

def delete_account(account_id):
    conn = get_connection()
    if not conn: return False
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM accounts WHERE id=%s", (account_id,))
        conn.commit()
        return True
    finally:
        cursor.close()
        conn.close()


# ===================================================================
# CATEGORIES MANAGEMENT
# ===================================================================
def save_category(category_name, description):
    conn = get_connection()
    if not conn: return False
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO categories (category_name, description) VALUES (%s, %s)", (category_name, description))
        conn.commit()
        return True
    except Error as e:
        print(f"Error saving category: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def get_categories_dataframe():
    conn = get_connection()
    if not conn: return pd.DataFrame()
    try:
        return pd.read_sql("SELECT * FROM categories", conn)
    finally:
        conn.close()

def get_categories():
    """Returns a dictionary mapping category names to their IDs."""
    conn = get_connection()
    if not conn: return {}
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id, category_name FROM categories")
        return {row['category_name']: row['id'] for row in cursor.fetchall()}
    finally:
        cursor.close()
        conn.close()

def get_category_id_map():
    conn = get_connection()
    if not conn: return {}
    try:
        df = pd.read_sql("SELECT id, category_name FROM categories", conn)
        return dict(zip(df["category_name"], df["id"]))
    finally:
        conn.close()

def update_category(category_id, category_name, description):
    conn = get_connection()
    if not conn: return False
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE categories SET category_name=%s, description=%s WHERE id=%s", (category_name, description, category_id))
        conn.commit()
        return True
    finally:
        cursor.close()
        conn.close()

def delete_category(category_id):
    conn = get_connection()
    if not conn: return False
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM categories WHERE id=%s", (category_id,))
        conn.commit()
        return True
    finally:
        cursor.close()
        conn.close()


# ===================================================================
# COMMON MERCHANTS & AI RULES MANAGEMENT
# ===================================================================
def check_common_merchant(raw_desc):
    """Uses SQL LIKE matching to find existing merchant rules and category associations."""
    conn = get_connection()
    if not conn: return None
    cursor = conn.cursor(dictionary=True)
    
    query = """
        SELECT cm.*, c.category_name 
        FROM common_merchants cm
        JOIN categories c ON cm.category_id = c.id
        WHERE %s LIKE cm.raw_pattern 
        LIMIT 1
    """
    try:
        cursor.execute(query, (raw_desc,))
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()

def save_common_merchant(raw_pattern, clean_name, category_id, score, is_sub):
    """Saves a new AI-generated or user-defined merchant rule into common_merchants."""
    conn = get_connection()
    if not conn: return None
    cursor = conn.cursor()
    
    query = """
        INSERT INTO common_merchants 
        (raw_pattern, clean_merchant_name, category_id, default_impulse_score, is_subscription)
        VALUES (%s, %s, %s, %s, %s)
    """
    try:
        cursor.execute(query, (raw_pattern, clean_name, category_id, score, is_sub))
        conn.commit()
        return cursor.lastrowid
    except Error as e:
        print(f"Error saving common merchant: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def get_merchants_dataframe():
    conn = get_connection()
    if not conn: return pd.DataFrame()
    try:
        query = """
            SELECT m.id, m.raw_pattern, m.clean_merchant_name, c.category_name, m.default_impulse_score, m.is_subscription 
            FROM common_merchants m 
            JOIN categories c ON m.category_id = c.id
        """
        return pd.read_sql(query, conn)
    finally:
        conn.close()

def update_merchant_rule(rule_id, raw_pattern, clean_name, category_id, score, is_sub):
    conn = get_connection()
    if not conn: return False
    cursor = conn.cursor()
    try:
        query = """
            UPDATE common_merchants 
            SET raw_pattern=%s, clean_merchant_name=%s, category_id=%s, default_impulse_score=%s, is_subscription=%s 
            WHERE id=%s
        """
        cursor.execute(query, (raw_pattern, clean_name, category_id, score, is_sub, rule_id))
        conn.commit()
        return True
    finally:
        cursor.close()
        conn.close()