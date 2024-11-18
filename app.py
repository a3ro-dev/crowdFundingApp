import streamlit as st
from datetime import datetime
import libs.db_con as db_con
import libs.uid_gen as uid_gen

# Initialize database and UID generator
db_wrapper = db_con.DBWrapper()
uid_generator = uid_gen.UIDGen(db_wrapper)

def main():
    # Set page configuration
    st.set_page_config(
        page_title="Crowdfunding Portal",
        page_icon="💰",
        layout="centered",
        initial_sidebar_state="collapsed",
    )

    # Theme toggle
    theme = st.sidebar.selectbox("Select Theme", ["Light", "Dark"])
    if theme == "Light":
        st.markdown(
            """
            <style>
            .main {
                background-color: #FEFCFF;
                color: black;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <style>
            .main {
                background-color: #000000;
                color: white;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

    # Header
    st.title("Welcome to the Crowdfunding Portal of Akshat Singh Kushwaha")
    st.write("We appreciate your presence.")

    # Admin button
    if st.button("Admin"):
        st.write("Admin login functionality to be implemented.")

    # Main navigation
    option = st.selectbox("Choose an option:", ["Buy Shares", "Verify UID"])

    if option == "Buy Shares":
        buy_shares()
    elif option == "Verify UID":
        verify_uid()

def buy_shares():
    st.header("Buy Shares")

    # User inputs
    full_name = st.text_input("Full Name", "")
    phone_number = st.text_input("Phone Number", "")

    # Validate phone number
    if phone_number and (not phone_number.isdigit() or len(phone_number) != 10):
        st.error("Please enter a valid 10-digit phone number.")

    # Investment amount
    if 'investment' not in st.session_state:
        st.session_state['investment'] = 0

    if st.button("Add ₹500"):
        st.session_state['investment'] += 500

    st.write(f"Amount to Invest: ₹{st.session_state['investment']}")

    # Live resale value
    st.write("Live Resale Value: ₹480")

    # Certificate type selection
    certificate_type = st.selectbox("Choose Certificate Type:", ["Small Card (₹40)", "A4 Sized Certificate (₹80)"])

    # Terms and conditions
    agree_tnc = st.checkbox("I agree to the Terms and Conditions")
    agree_non_refund = st.checkbox("I agree that the amount is non-refundable except by the founder's will")
    st.markdown("[View Terms and Conditions](terms_and_conditions.md)")

    # Proceed button
    if st.button("Proceed"):
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
            resale_value = 480  # Constant for now
            email = None  # Optional, not collected here

            # Certificate cost
            cert_cost = 40 if certificate_type == "Small Card (₹40)" else 80
            total_payable = amount_invested + cert_cost

            # Add user to the database
            try:
                db_wrapper.add_user(uid, full_name, phone_number, amount_invested, date_of_investment, email, resale_value)
                db_wrapper.update_certificate_type(uid, certificate_type)
                st.success("Account created successfully!")
                st.write(f"Your UID is: `{uid}`")
                st.write("Please note that your certificate of ownership will reach you in 10 days to a month.")
                st.write(f"Total Payable Amount (including certificate cost): ₹{total_payable}")
                st.write("Wait 4-8 hours for the UID to reflect on the verification page.")
                # Reset session state
                st.session_state['investment'] = 0
            except Exception as e:
                st.error(f"An error occurred: {e}")

def verify_uid():
    st.header("Verify UID")

    uid = st.text_input("Enter your UID:")

    if st.button("Verify"):
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
        else:
            st.error("UID not found. Please check and try again.")

if __name__ == "__main__":
    main()
    db_wrapper.close()