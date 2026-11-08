# app.py
import logging
import os
from datetime import date
import pandas as pd
import streamlit as st

from src import db_manager
from src.processor import process_bank_csv

# Module-level logger inheriting configuration
logger = logging.getLogger(__name__)

# Streamlit Page Setup
st.set_page_config(
    page_title="Personal Finance Hub Setup", page_icon="💳", layout="wide"
)

st.title("⚙️ Personal Finance Base Setup")
st.markdown("Manage your baseline accounts, categories, merchant rules, and statement imports.")

tab1, tab2, tab3, tab4 = st.tabs(
    ["1. Accounts", "2. Categories", "3. Merchant Rules", "4. CSV Import"]
)

# ===================================================================
# TAB 1: ACCOUNTS
# ===================================================================
with tab1:
    st.subheader("Add New Account")
    with st.form("account_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            full_name = st.text_input(
                "Full Account Name",
                placeholder="e.g. Commonwealth Bank Everyday Access",
            )
            nickname = st.text_input(
                "Nickname", placeholder="e.g. CBA Everyday"
            )
            institution = st.text_input(
                "Institution / Bank", placeholder="e.g. CBA"
            )
        with col2:
            acc_type = st.selectbox(
                "Account Type",
                ["Everyday", "Savings", "Credit Card", "Investment"],
            )
            date_added = st.date_input("Date Added", value=date.today())

        if st.form_submit_button("Save Account"):
            clean_full = full_name.strip()
            clean_nick = nickname.strip()
            clean_inst = institution.strip()

            if clean_full and clean_nick:
                try:
                    logger.info(f"Attempting to add account: '{clean_nick}'")
                    success = db_manager.save_account(
                        full_account_name=clean_full,
                        nickname=clean_nick,
                        account_type=acc_type,
                        institution_name=clean_inst,
                        date_added=date_added
                    )
                    if success:
                        logger.info(f"Successfully added account: '{clean_nick}' (Type: {acc_type})")
                        st.success(f"Account '{clean_nick}' saved!")
                        st.rerun()
                    else:
                        st.error("Failed to save account. Check database connection or logs.")
                except Exception as e:
                    logger.exception(f"Unexpected error creating account '{clean_nick}': {e}")
                    st.error("An unexpected error occurred. Check logs.")
            else:
                logger.warning("Account creation submission failed: Missing required fields.")
                st.warning("Both Full Account Name and Nickname are required.")

    st.markdown("---")
    st.subheader("Existing Accounts")

    try:
        df_acc = db_manager.get_accounts_dataframe()

        if not df_acc.empty:
            df_display = df_acc.rename(
                columns={
                    "id": "ID",
                    "full_account_name": "Full Account Name",
                    "nickname": "Nickname",
                    "account_type": "Type",
                    "institution_name": "Institution",
                    "is_active": "Active Status",
                    "date_added": "Date Added",
                    "created_at": "Created At",
                }
            )
            st.dataframe(df_display, use_container_width=True)

            col_edit, col_del = st.columns(2)
            with col_edit:
                with st.expander("✏️ Edit Account"):
                    acc_to_edit = st.selectbox(
                        "Select Account to Edit",
                        df_acc["id"].tolist(),
                        format_func=lambda x: f"ID {x}: {df_acc.loc[df_acc['id'] == x, 'nickname'].values[0]}",
                        key="edit_acc_select",
                    )
                    row = df_acc[df_acc["id"] == acc_to_edit].iloc[0]

                    edit_full = st.text_input(
                        "Full Account Name", value=row["full_account_name"]
                    )
                    edit_nick = st.text_input(
                        "Nickname", value=row["nickname"]
                    )
                    edit_inst = st.text_input(
                        "Institution", value=row["institution_name"] or ""
                    )
                    edit_type = st.selectbox(
                        "Type",
                        ["Everyday", "Savings", "Credit Card", "Investment"],
                        index=[
                            "Everyday",
                            "Savings",
                            "Credit Card",
                            "Investment",
                        ].index(row["account_type"]),
                    )

                    if st.button("Update Account"):
                        try:
                            logger.info(f"Updating account ID {acc_to_edit} ('{edit_nick.strip()}')")
                            db_manager.update_account(
                                account_id=acc_to_edit,
                                full_account_name=edit_full.strip(),
                                nickname=edit_nick.strip(),
                                institution_name=edit_inst.strip(),
                                account_type=edit_type
                            )
                            logger.info(f"Account ID {acc_to_edit} updated successfully.")
                            st.success("Account updated!")
                            st.rerun()
                        except Exception as e:
                            logger.exception(f"Error updating account ID {acc_to_edit}: {e}")
                            st.error(f"Error updating account: {e}")

            with col_del:
                with st.expander("🗑️ Delete Account"):
                    acc_to_del = st.selectbox(
                        "Select Account to Delete",
                        df_acc["id"].tolist(),
                        format_func=lambda x: f"ID {x}: {df_acc.loc[df_acc['id'] == x, 'nickname'].values[0]}",
                        key="del_acc_select",
                    )
                    if st.button("Confirm Delete Account", type="primary"):
                        try:
                            logger.info(f"Attempting to delete account ID {acc_to_del}")
                            db_manager.delete_account(acc_to_del)
                            logger.info(f"Account ID {acc_to_del} deleted successfully.")
                            st.success("Account deleted!")
                            st.rerun()
                        except Exception as e:
                            logger.exception(f"Error deleting account ID {acc_to_del}: {e}")
                            st.error(f"Error deleting account: {e}")
        else:
            st.info("No accounts found.")
    except Exception as e:
        logger.exception(f"Error retrieving existing accounts: {e}")
        st.error(f"Could not load accounts: {e}")

# ===================================================================
# TAB 2: CATEGORIES
# ===================================================================
with tab2:
    st.subheader("Add Expense Category")
    with st.form("category_form", clear_on_submit=True):
        cat_name = st.text_input(
            "Category Name", placeholder="e.g. Subscriptions"
        )
        cat_desc = st.text_area(
            "Description", placeholder="e.g. Recurring software, streaming"
        )

        if st.form_submit_button("Save Category"):
            clean_cat = cat_name.strip()
            clean_desc = cat_desc.strip()

            if clean_cat:
                try:
                    logger.info(f"Adding new category: '{clean_cat}'")
                    success = db_manager.save_category(clean_cat, clean_desc)
                    if success:
                        logger.info(f"Category '{clean_cat}' saved successfully.")
                        st.success(f"Category '{clean_cat}' added!")
                        st.rerun()
                    else:
                        st.error("Failed to save category. It may already exist.")
                except Exception as e:
                    logger.exception(f"Unexpected error adding category '{clean_cat}': {e}")
                    st.error("Unexpected error occurred. Check logs.")
            else:
                logger.warning("Category submission failed: Name was empty.")
                st.warning("Category Name is required.")

    st.markdown("---")
    st.subheader("Existing Categories")

    try:
        df_cat = db_manager.get_categories_dataframe()

        if not df_cat.empty:
            df_cat_display = df_cat.rename(
                columns={
                    "id": "ID",
                    "category_name": "Category Name",
                    "description": "Description",
                }
            )
            st.dataframe(df_cat_display, use_container_width=True)

            col_edit_c, col_del_c = st.columns(2)
            with col_edit_c:
                with st.expander("✏️ Edit Category"):
                    cat_to_edit = st.selectbox(
                        "Select Category to Edit",
                        df_cat["id"].tolist(),
                        format_func=lambda x: f"ID {x}: {df_cat.loc[df_cat['id'] == x, 'category_name'].values[0]}",
                        key="edit_cat_select",
                    )
                    row_c = df_cat[df_cat["id"] == cat_to_edit].iloc[0]

                    edit_c_name = st.text_input(
                        "Category Name", value=row_c["category_name"]
                    )
                    edit_c_desc = st.text_area(
                        "Description", value=row_c["description"] or ""
                    )

                    if st.button("Update Category"):
                        try:
                            logger.info(f"Updating category ID {cat_to_edit} ('{edit_c_name.strip()}')")
                            db_manager.update_category(cat_to_edit, edit_c_name.strip(), edit_c_desc.strip())
                            logger.info(f"Category ID {cat_to_edit} updated successfully.")
                            st.success("Category updated!")
                            st.rerun()
                        except Exception as e:
                            logger.exception(f"Error updating category ID {cat_to_edit}: {e}")
                            st.error(f"Error updating category: {e}")

            with col_del_c:
                with st.expander("🗑️ Delete Category"):
                    cat_to_del = st.selectbox(
                        "Select Category to Delete",
                        df_cat["id"].tolist(),
                        format_func=lambda x: f"ID {x}: {df_cat.loc[df_cat['id'] == x, 'category_name'].values[0]}",
                        key="del_cat_select",
                    )
                    if st.button("Confirm Delete Category", type="primary"):
                        try:
                            logger.info(f"Attempting to delete category ID {cat_to_del}")
                            db_manager.delete_category(cat_to_del)
                            logger.info(f"Category ID {cat_to_del} deleted successfully.")
                            st.success("Category deleted!")
                            st.rerun()
                        except Exception as e:
                            logger.exception(f"Error deleting category ID {cat_to_del}: {e}")
                            st.error(f"Error deleting category: {e}")
        else:
            st.info("No categories found.")
    except Exception as e:
        logger.exception(f"Error loading categories: {e}")
        st.error(f"Could not load categories: {e}")

# ===================================================================
# TAB 3: MERCHANT RULES
# ===================================================================
with tab3:
    st.subheader("Add Merchant Pattern for Ollama")

    cat_map = db_manager.get_category_id_map()

    with st.form("merchant_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            raw_pattern = st.text_input(
                "Raw Pattern / Search Term",
                placeholder="e.g. WOOLWORTHS% or UBER",
            )
            clean_name = st.text_input(
                "Clean Merchant Name", placeholder="e.g. Woolworths"
            )
        with col2:
            selected_cat = st.selectbox(
                "Category", list(cat_map.keys()) if cat_map else []
            )
            impulse_score = st.slider("Impulse Score (1-10)", 1, 10, 3)
            is_sub = st.checkbox("Is Subscription?")

        if st.form_submit_button("Save Merchant Pattern"):
            clean_pattern = raw_pattern.strip()
            clean_m_name = clean_name.strip()

            if clean_pattern and clean_m_name and selected_cat:
                try:
                    logger.info(f"Adding merchant rule: Pattern '{clean_pattern}' -> '{clean_m_name}'")
                    success = db_manager.save_common_merchant(
                        raw_pattern=clean_pattern,
                        clean_name=clean_m_name,
                        category_id=cat_map[selected_cat],
                        score=impulse_score,
                        is_sub=is_sub
                    )
                    if success:
                        logger.info(f"Merchant rule for '{clean_m_name}' saved successfully.")
                        st.success("Merchant pattern saved!")
                        st.rerun()
                    else:
                        st.error("Failed to save merchant pattern. Pattern might already exist.")
                except Exception as e:
                    logger.exception(f"Unexpected error saving merchant rule: {e}")
                    st.error("Unexpected error occurred. Check logs.")
            else:
                logger.warning("Merchant pattern submission failed: Missing required fields.")
                st.warning("Please fill in all required fields.")

    st.markdown("---")
    st.subheader("Existing Merchant Patterns")

    try:
        df_merchants = db_manager.get_merchants_dataframe()

        if not df_merchants.empty:
            df_m_display = df_merchants.rename(
                columns={
                    "id": "ID",
                    "raw_pattern": "Search Pattern",
                    "clean_merchant_name": "Merchant Name",
                    "category_name": "Category",
                    "default_impulse_score": "Impulse Score",
                    "is_subscription": "Subscription?",
                }
            )
            st.dataframe(df_m_display, use_container_width=True)

            col_edit_m, col_del_m = st.columns(2)
            with col_edit_m:
                with st.expander("✏️ Edit Merchant Pattern"):
                    m_to_edit = st.selectbox(
                        "Select Pattern to Edit",
                        df_merchants["id"].tolist(),
                        format_func=lambda x: f"ID {x}: {df_merchants.loc[df_merchants['id'] == x, 'raw_pattern'].values[0]}",
                        key="edit_m_select",
                    )
                    row_m = df_merchants[df_merchants["id"] == m_to_edit].iloc[0]

                    edit_pat = st.text_input(
                        "Search Pattern", value=row_m["raw_pattern"]
                    )
                    edit_cname = st.text_input(
                        "Merchant Name", value=row_m["clean_merchant_name"]
                    )
                    edit_m_cat = st.selectbox(
                        "Category",
                        list(cat_map.keys()),
                        index=list(cat_map.keys()).index(
                            row_m["category_name"]
                        ),
                    )
                    edit_imp = st.slider(
                        "Impulse Score",
                        1,
                        10,
                        int(row_m["default_impulse_score"]),
                    )
                    edit_sub = st.checkbox(
                        "Subscription?", value=bool(row_m["is_subscription"])
                    )

                    if st.button("Update Merchant Pattern"):
                        try:
                            logger.info(f"Updating merchant pattern ID {m_to_edit}")
                            db_manager.update_merchant_rule(
                                rule_id=m_to_edit,
                                raw_pattern=edit_pat.strip(),
                                clean_name=edit_cname.strip(),
                                category_id=cat_map[edit_m_cat],
                                score=edit_imp,
                                is_sub=edit_sub
                            )
                            logger.info(f"Merchant pattern ID {m_to_edit} updated successfully.")
                            st.success("Pattern updated!")
                            st.rerun()
                        except Exception as e:
                            logger.exception(f"Error updating merchant pattern ID {m_to_edit}: {e}")
                            st.error(f"Error updating pattern: {e}")

            with col_del_m:
                with st.expander("🗑️ Delete Merchant Pattern"):
                    m_to_edit_del = st.selectbox(
                        "Select Pattern to Delete",
                        df_merchants["id"].tolist(),
                        format_func=lambda x: f"ID {x}: {df_merchants.loc[df_merchants['id'] == x, 'raw_pattern'].values[0]}",
                        key="del_m_select",
                    )
                    if st.button("Confirm Delete Pattern", type="primary"):
                        try:
                            logger.info(f"Attempting to delete merchant pattern ID {m_to_edit_del}")
                            db_manager.delete_merchant_rule(m_to_edit_del)
                            logger.info(f"Merchant pattern ID {m_to_edit_del} deleted successfully.")
                            st.success("Pattern deleted!")
                            st.rerun()
                        except Exception as e:
                            logger.exception(f"Error deleting merchant pattern ID {m_to_edit_del}: {e}")
                            st.error(f"Error deleting pattern: {e}")
        else:
            st.info("No merchant patterns found.")
    except Exception as e:
        logger.exception(f"Error loading merchant patterns: {e}")
        st.error(f"Could not load merchant patterns: {e}")

# ===================================================================
# TAB 4: CSV IMPORT
# ===================================================================
with tab4:
    st.subheader("📥 Upload & Process Bank Statement")
    st.markdown("Select an account and upload your statement CSV. Dates are automatically detected from the file.")

    try:
        df_acc_import = db_manager.get_accounts_dataframe()
        if df_acc_import.empty:
            st.warning("⚠️ Please create an account in the '1. Accounts' tab before importing statements.")
        else:
            selected_acc_id = st.selectbox(
                "Select Target Account",
                df_acc_import["id"].tolist(),
                format_func=lambda x: f"{df_acc_import.loc[df_acc_import['id'] == x, 'nickname'].values[0]} ({df_acc_import.loc[df_acc_import['id'] == x, 'institution_name'].values[0]})",
                key="import_acc_select"
            )
            
            selected_acc_row = df_acc_import[df_acc_import["id"] == selected_acc_id].iloc[0]
            account_name_slug = selected_acc_row["nickname"].replace(" ", "_")

            uploaded_file = st.file_uploader("Choose Bank Statement CSV", type=["csv"])

            if uploaded_file is not None:
                try:
                    df_preview = pd.read_csv(uploaded_file)
                    st.write("### CSV Preview (First 5 Rows)")
                    st.dataframe(df_preview.head(), use_container_width=True)

                    # Normalize columns to lowercase for safe detection
                    cols_lower = [str(c).strip().lower() for c in df_preview.columns]
                    date_col_candidates = [df_preview.columns[i] for i, c in enumerate(cols_lower) if 'date' in c]

                    if not date_col_candidates:
                        st.error("❌ Could not automatically detect a 'date' column in your CSV. Ensure headers include 'date'.")
                    else:
                        date_col = date_col_candidates[0]
                        parsed_dates = pd.to_datetime(df_preview[date_col], dayfirst=True, errors='coerce')
                        
                        if parsed_dates.isna().all():
                            st.error(f"❌ Could not parse dates from column '{date_col}'. Check date formatting.")
                        else:
                            min_date = parsed_dates.min().strftime('%Y-%m-%d')
                            max_date = parsed_dates.max().strftime('%Y-%m-%d')

                            st.info(f"📅 Detected Statement Period: **{min_date}** to **{max_date}**")

                            target_filename = f"{min_date}-{max_date}-{account_name_slug}.csv"
                            
                            if st.button("🚀 Process & Import Transactions", type="primary"):
                                os.makedirs("uploads", exist_ok=True)
                                file_path = os.path.join("uploads", target_filename)

                                uploaded_file.seek(0)
                                with open(file_path, "wb") as f:
                                    f.write(uploaded_file.getbuffer())

                                logger.info(f"Saved uploaded statement to {file_path}")
                                st.success(f"File archived as `{target_filename}`. Running processor & Ollama categorization...")

                                with st.spinner("Processing transactions..."):
                                    process_bank_csv(file_path)
                                
                                st.success("🎉 Import complete! Check your logs and database.")
                except Exception as parse_err:
                    logger.exception(f"Error parsing uploaded CSV: {parse_err}")
                    st.error(f"Error reading CSV file: {parse_err}")

    except Exception as e:
        logger.exception(f"Error loading accounts for import tab: {e}")
        st.error(f"Could not load accounts: {e}")