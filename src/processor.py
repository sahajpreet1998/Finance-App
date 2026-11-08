# processor.py
import os
import pandas as pd
import logging
import ollama
import json
import re
import hashlib
from datetime import datetime
from config import AI_MODEL
import db_manager as db

# Initialize the logger for this specific file
logger = logging.getLogger(__name__)

def validate_and_log_file(file_path):
    """Checks the filename format and saves the file to the mysql log table."""
    filename = os.path.basename(file_path)

    # 1. Regex validation for YYYY-MM-DD-YYYY-MM-DD-AccountName.csv
    pattern = r"^(\d{4}-\d{2}-\d{2})-(\d{4}-\d{2}-\d{2})-(.+)\.csv$"
    match = re.match(pattern, filename)

    if not match:
        logger.error(f"Invalid filename format: '{filename}'")
        logger.error("Required format: YYYY-MM-DD-YYYY-MM-DD-AccountName.csv")
        return None
    
    start_str, end_str, account_name = match.groups()

    # 2. Date Logical Check (Start to be before end date)
    try:
        start_date = datetime.strptime(start_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_str, '%Y-%m-%d')

        if start_date >= end_date:
            logger.error(f"Date Error: Start Date ({start_str}) must be BEFORE the End Date ({end_str})")
            return None
        
    except Exception:
        logger.error(f"Date Error: Dates in filename are not valid calendar dates.")
        return None
    
    # 3. Account Check
    logger.debug(f"Checking database for account: '{account_name}'")
    account_id, suggestions = db.get_account_id(account_name)
    
    if not account_id:
        logger.error(f"Account '{account_name}' not recognized.")
        if suggestions:
            logger.info(f"Available accounts in DB: {', '.join(suggestions)}")
        return None
    
    # 4. Check for Duplicate File
    if not db.is_file_new(filename):
        logger.warning(f"File '{filename}' already exists in DB. Skipping heavy processing.")
        return None
    
    # 5. Log File Content to DB
    try:
        logger.info(f"Reading new file content for: {filename}")
        with open(file_path, 'rb') as f:
            file_content = f.read()

        db.log_file_upload(filename, file_content, start_date, end_date, account_name)
        logger.info(f"File '{filename}' logged successfully.")

    except Exception as e:
        logger.error(f"Failed to read or log file '{filename}': {e}")
        return None
    
    return account_id

def process_bank_csv(file_path):
    account_id = validate_and_log_file(file_path)

    if account_id:
        logger.info(f"Starting transaction import for Account ID: {account_id}")
        logger.info(f"Loading CSV file: {file_path}")

        try:
            # 1. Load and normalize CSV headers
            df = pd.read_csv(file_path)
            df.columns = df.columns.str.strip().str.lower()
            
            if 'date' not in df.columns or 'description' not in df.columns or 'amount' not in df.columns:
                logger.error("CSV is missing required columns ('date', 'description', 'amount').")
                return

            df['date'] = pd.to_datetime(df['date'], dayfirst=True).dt.strftime('%Y-%m-%d')
            logger.info(f"Found {len(df)} transactions to process.")

            for index, row in df.iterrows():
                try:
                    raw_desc = str(row['description']).strip()
                    date = row['date']
                    
                    # Clean amount string (remove $, commas, whitespace)
                    clean_amount_str = str(row['amount']).replace('$', '').replace(',', '').strip()
                    amount = float(clean_amount_str)

                    # Skip income (positive numbers) if focusing strictly on expenses
                    if amount >= 0:
                        logger.debug(f"Skipping income: {raw_desc} (+{amount})")
                        continue

                    # Generate unique transaction hash for duplicate prevention
                    hash_input = f"{account_id}_{date}_{amount}_{raw_desc}"
                    tx_hash = hashlib.sha256(hash_input.encode('utf-8')).hexdigest()

                    if db.is_transaction_duplicate(tx_hash):
                        logger.debug(f"Duplicate transaction skipped: {date} | {raw_desc} | {amount}")
                        continue

                    logger.info(f"Row {index}: Processing '{raw_desc}'")
    
                    # 2. Check MySQL Lookup Table first
                    existing_mapping = db.check_merchant(raw_desc)

                    if existing_mapping:
                        merchant_id = existing_mapping['id']
                        logger.info(f"Found in Lookup: {existing_mapping['category']}")
                    else:
                        logger.warning(f"New Merchant: '{raw_desc}'. Consulting AI ({AI_MODEL})...")
                        
                        prompt = f"""
                            Analyze this bank transaction: "{raw_desc}"
                            Return ONLY a JSON object with these exact keys:
                            "merchant": (cleaner name of the store),
                            "category": (one word category like Groceries, Entertainment, etc),
                            "impulse_score": (integer 1-10),
                            "is_subscription": (boolean)
                        """
                        
                        response = ollama.chat(
                            model=AI_MODEL,
                            messages=[{'role': 'user', 'content': prompt}],
                            format='json'
                        )
                        
                        ai_data = json.loads(response['message']['content'])

                        # Safety Net: Use .get() to prevent crashes if AI misses a key
                        clean_name = ai_data.get('merchant', raw_desc)
                        category = ai_data.get('category', 'Uncategorized')
                        score = ai_data.get('impulse_score', 5)
                        is_sub = ai_data.get('is_subscription', False)

                        # Save to MySQL Lookup Table
                        merchant_id = db.save_merchant(
                            raw_desc, 
                            clean_name, 
                            category, 
                            score, 
                            is_sub
                        )
                        logger.info(f"AI categorized as: {category} (Score: {score})")

                    if merchant_id is None:
                        raise ValueError("Could not resolve or generate a valid merchant_lookup_id.")
            
                    # Save the spending record with tx_hash
                    db.save_transaction(
                        date=date, 
                        raw_desc=raw_desc, 
                        amount=amount, 
                        account_id=account_id, 
                        merchant_lookup_id=merchant_id,
                        tx_hash=tx_hash
                    )
                    logger.debug(f"Transaction saved: {date} | {raw_desc} | {amount}")
                
                except Exception as row_error:
                    logger.error(f"Failed at row {index} ({row['description']}): {row_error}")
                    continue

        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
        except Exception as e:
            logger.error(f"Critical Error processing CSV: {e}", exc_info=True)

        logger.info("Finished processing CSV.")