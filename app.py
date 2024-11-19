# app.py

import streamlit as st
from datetime import datetime
import libs.db_con as db_con
import libs.uid_gen as uid_gen
import json  # For handling JSON data in transactions

# Initialize database and UID generator
db_wrapper = db_con.DBWrapper()
uid_generator = uid_gen.UIDGen(db_wrapper)

def main():
    # Set page configuration
    st.set_page_config(
        page_title="Crowdfunding Portal",
        page_icon="💰",
        layout="centered",
    )

    # Initialize session state variables
    if 'current_page' not in st.session_state:
        st.session_state['current_page'] = 'home'

    # Header
    st.title("Welcome to the Crowdfunding Portal of Akshat Singh Kushwaha")
    st.write("We appreciate your presence.")

    # Navigation logic
    if st.session_state['current_page'] == 'home':
        home_page()
    elif st.session_state['current_page'] == 'buy':
        buy_shares()
    elif st.session_state['current_page'] == 'verify':
        verify_uid()

def home_page():
    # Centered Buy and Verify buttons
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div style="text-align: center;">', unsafe_allow_html=True)
        buy_clicked = st.button("Buy", key="buy_button")
        verify_clicked = st.button("Verify", key="verify_button")
        st.markdown('</div>', unsafe_allow_html=True)
    
    if buy_clicked:
        st.session_state['current_page'] = 'buy'
        st.rerun()
    elif verify_clicked:
        st.session_state['current_page'] = 'verify'
        st.rerun()

def buy_shares():
    st.header("Profit Shares* Management")

    # Back button
    if st.button("Back"):
        st.session_state['current_page'] = 'home'
        st.rerun()

    # User type selection
    user_type = st.radio("Are you a new or existing investor?", ["New Investor", "Existing Investor"])

    if user_type == "New Investor":
        new_user_investment()
    else:
        existing_user_management()

def new_user_investment():
    st.subheader("New Investor Registration")

    # User inputs
    full_name = st.text_input("Full Name", key="new_full_name")
    phone_number = st.text_input("Phone Number", key="new_phone_number")

    # Validate phone number
    if phone_number and (not phone_number.isdigit() or len(phone_number) != 10):
        st.error("Please enter a valid 10-digit phone number.")

    # Secret code verification
    secret_code = st.text_input("Enter the secret code to proceed:", key="new_secret_code", type="password")
    if secret_code != 'swascat':
        st.error("Invalid secret code.")

    # Proceed only if the secret code is correct
    if secret_code == 'swascat':
        # Investment amount
        if 'investment' not in st.session_state:
            st.session_state['investment'] = 0

        if st.button("Add ₹500", key="new_add_500"):
            st.session_state['investment'] += 500

        # Calculate number of shares and resale value
        num_shares = st.session_state['investment'] // 500
        resale_value = 480 * num_shares

        st.write(f"Amount to Invest: ₹{st.session_state['investment']}")
        st.write(f"Number of Profit Shares*: {num_shares}")
        st.write(f"Live Resale Value: ₹{resale_value} (₹480 per ₹500 profit share*)")

        # Certificate type selection
        certificate_type = st.selectbox("Choose Certificate Type:", ["Small Card (₹40)", "A4 Sized Certificate (₹80)"], key="new_cert_type")
        cert_cost = 40 if "Small Card" in certificate_type else 80

        # Cost breakdown
        total_payable = st.session_state['investment'] + cert_cost
        st.markdown("### Cost Breakdown:")
        st.markdown(f"""
        Investment Amount  → ₹{st.session_state['investment']}
        Certificate Cost   → ₹{cert_cost}
        ________________________
        **Total Payable    → ₹{total_payable}**
        """)

        # Terms and conditions
        agree_tnc = st.checkbox("I agree to the Terms and Conditions", key="new_agree_tnc")
        agree_non_refund = st.checkbox("I agree that the amount is non-refundable except by the founder's will", key="new_agree_non_refund")
        st.markdown("[View Terms and Conditions](assets/terms_and_conditions.md)", unsafe_allow_html=True)

        # Proceed button
        if st.button("Proceed", key="new_proceed"):
            if not full_name or not phone_number:
                st.error("Please fill in all required fields.")
            elif st.session_state['investment'] == 0:
                st.error("Please add the amount to invest.")
            elif not agree_tnc or not agree_non_refund:
                st.error("Please agree to the terms and conditions.")
            else:
                # Generate UID
                uid = uid_generator.generate_uid()

                # Save data to the database
                date_of_investment = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                amount_invested = st.session_state['investment']
                email = None  # Optional, not collected here

                # Add user to the database
                try:
                    db_wrapper.add_user(uid, full_name, phone_number, amount_invested, date_of_investment, email, resale_value)
                    db_wrapper.update_certificate_type(uid, certificate_type)
                    # Log transaction
                    db_wrapper.add_transaction(uid, "investment", amount_invested, "Initial investment")
                    st.success("Account created successfully!")
                    st.write(f"Your UID is: `{uid}`")
                    st.write("Please note that your certificate of ownership will reach you in 10 days to a month.")
                    st.write(f"Total Payable Amount (including certificate cost): ₹{total_payable}")
                    st.write("Wait 4-8 hours for the UID to reflect on the verification page.")
                    # Reset session state
                    st.session_state['investment'] = 0
                except Exception as e:
                    st.error(f"An error occurred: {e}")

def existing_user_management():
    st.subheader("Existing Investor Portal")

    # Check if 'uid_verified' is in session_state
    if 'uid_verified' not in st.session_state:
        st.session_state.uid_verified = False

    # UID input and verification
    if not st.session_state.uid_verified:
        uid = st.text_input("Enter your UID:", key="existing_uid")
        if st.button("Verify UID", key="verify_uid"):
            user = db_wrapper.get_user_by_uid(uid)
            if user:
                # Secret code verification
                secret_code = st.text_input("Enter the secret code to proceed:", key="existing_secret_code", type="password")
                if secret_code != 'swascat':
                    st.error("Invalid secret code.")
                else:
                    st.success("UID verified!")
                    st.session_state.uid_verified = True
                    st.session_state.uid = uid
                    st.session_state.user_data = user
                    # Log verification as a transaction
                    db_wrapper.add_transaction(uid, "verification", 0, "User checked account details")
                    st.experimental_rerun()
            else:
                st.error("UID not found. Please check and try again.")
    else:
        user = st.session_state.user_data
        st.write(f"**Name:** {user[1]}")
        st.write(f"**Current Investment:** ₹{user[4]}")
        st.write(f"**Current Resale Value:** ₹{user[6]}")

        # Action Selection
        action = st.radio("Select Action:", ["Reinvest", "Transfer Investment"], key="existing_action")

        if action == "Reinvest":
            reinvestment(st.session_state.uid, user)
        elif action == "Transfer Investment":
            transfer_investment(st.session_state.uid, user)

        # Option to reset verification
        if st.button("Log out", key="reset_verification"):
            st.session_state.uid_verified = False
            st.session_state.uid = ''
            st.session_state.user_data = None
            st.rerun()

def reinvestment(uid, user):
    st.subheader("Reinvestment")

    # Secret code verification
    secret_code = st.text_input("Enter the secret code to proceed:", key="reinvest_secret_code", type="password")
    if secret_code != 'swascat':
        st.error("Invalid secret code.")
    else:
        st.write(f"**Name:** {user[1]}")
        st.write(f"**Current Investment:** ₹{user[4]}")
        st.write(f"**Current Resale Value:** ₹{user[6]}")

        if 'additional_investment' not in st.session_state:
            st.session_state['additional_investment'] = 0

        if st.button("Add ₹500", key="reinvest_add_500"):
            st.session_state['additional_investment'] += 500

        additional_investment = st.session_state['additional_investment']
        if additional_investment > 0:
            new_total_investment = user[4] + additional_investment
            num_shares = new_total_investment // 500
            new_resale_value = 480 * num_shares

            st.markdown("### Investment Summary:")
            st.write(f"Current Investment: ₹{user[4]}")
            st.write(f"Additional Investment: ₹{additional_investment}")
            st.write(f"New Total Investment: ₹{new_total_investment}")
            st.write(f"New Resale Value: ₹{new_resale_value}")

            if st.button("Confirm Reinvestment", key="confirm_reinvestment"):
                try:
                    # Update user investment and resale value
                    db_wrapper.update_investment(uid, new_total_investment, new_resale_value)
                    # Log transaction
                    db_wrapper.add_transaction(uid, "reinvestment", additional_investment, "Added additional investment")
                    st.success("Reinvestment successful!")
                    # Reset additional investment
                    st.session_state['additional_investment'] = 0
                    # Update user data
                    st.session_state.user_data = db_wrapper.get_user_by_uid(uid)
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"An error occurred: {e}")
        else:
            st.info("Click 'Add ₹500' to increase your investment.")

def transfer_investment(uid, user):
    st.subheader("Transfer Investment")

    # Secret code verification
    secret_code = st.text_input("Enter the secret code to proceed:", key="transfer_secret_code", type="password")
    if secret_code != 'swascat':
        st.error("Invalid secret code.")
    else:
        st.write(f"**Your Name:** {user[1]}")
        st.write(f"**Your Current Investment:** ₹{user[4]}")
        st.write(f"**Your Current Resale Value:** ₹{user[6]}")

        target_uid = st.text_input("Enter recipient's UID:", key="transfer_target_uid")
        if st.button("Verify Recipient UID", key="verify_recipient_uid"):
            target_user = db_wrapper.get_user_by_uid(target_uid)
            if target_user:
                st.success("Recipient UID verified!")
                st.write(f"**Recipient Name:** {target_user[1]}")
                st.write(f"**Recipient Current Investment:** ₹{target_user[4]}")
                st.write(f"**Recipient Current Resale Value:** ₹{target_user[6]}")

                transfer_amount = st.number_input("Enter amount to transfer (in multiples of ₹500):",
                                                  min_value=500, step=500, key="transfer_amount")

                if st.button("Confirm Transfer", key="confirm_transfer"):
                    if transfer_amount > user[4]:
                        st.error("Transfer amount exceeds your current investment.")
                    elif transfer_amount % 500 != 0:
                        st.error("Transfer amount must be in multiples of ₹500.")
                    else:
                        # Calculate new investment and resale values
                        sender_new_investment = user[4] - transfer_amount
                        sender_num_shares = sender_new_investment // 500
                        sender_new_resale = 480 * sender_num_shares

                        recipient_new_investment = target_user[4] + transfer_amount
                        recipient_num_shares = recipient_new_investment // 500
                        recipient_new_resale = 480 * recipient_num_shares

                        try:
                            # Update sender's data
                            db_wrapper.update_investment(uid, sender_new_investment, sender_new_resale)
                            db_wrapper.add_transaction(uid, "transfer_out", -transfer_amount,
                                                       f"Transferred to UID {target_uid}")

                            # Update recipient's data
                            db_wrapper.update_investment(target_uid, recipient_new_investment, recipient_new_resale)
                            db_wrapper.add_transaction(target_uid, "transfer_in", transfer_amount,
                                                       f"Received from UID {uid}")

                            st.success("Transfer successful!")
                            # Update user data
                            st.session_state.user_data = db_wrapper.get_user_by_uid(uid)
                            st.experimental_rerun()
                        except Exception as e:
                            st.error(f"An error occurred: {e}")
            else:
                st.error("Recipient UID not found.")

def verify_uid():
    st.header("Verify UID")

    # Back button
    if st.button("Back"):
        st.session_state['current_page'] = 'home'
        st.rerun()

    uid = st.text_input("Enter your UID:", key="verify_uid_input")

    if st.button("Verify UID", key="verify_uid_button"):
        user = db_wrapper.get_user_by_uid(uid)
        if user:
            # Display user information
            st.success("UID found!")
            st.write(f"**UID:** {user[0]}")
            st.write(f"**Name:** {user[1]}")
            st.write(f"**Amount Invested:** ₹{user[4]}")
            st.write(f"**Date of Investment:** {user[5]}")
            st.write(f"**Resale Value:** ₹{user[6]}")
            st.write(f"**Certificate Type:** {user[7]}")

            # Display transaction history
            transactions = db_wrapper.get_transactions(uid)
            if transactions:
                st.markdown("### Transaction History:")
                for txn in transactions:
                    st.write(f"**{txn['timestamp']}** - {txn['type'].capitalize()}: {txn['details']} (₹{txn['amount']})")
            else:
                st.write("No transactions found.")

            # Log verification as a transaction
            db_wrapper.add_transaction(uid, "verification", 0, "User verification")
        else:
            st.error("UID not found. Please check and try again.")

if __name__ == "__main__":
    main()
    db_wrapper.close()