# admin_panel.py
import streamlit as st
import libs.db_con as db_con
import os
import json
import pandas as pd
import psutil
import time
import plotly.graph_objects as go
import plotly.express as px
from fuzzywuzzy import process
from fuzzywuzzy import fuzz
from pathlib import Path

# Use environment variables for admin credentials
ADMIN_USERNAME = 'AKSHAT'  # Replace with os.environ.get("ADMIN_USERNAME")
ADMIN_PASSWORD = 'SWASCAT'  # Replace with os.environ.get("ADMIN_PASSWORD")

def admin_login():
    st.subheader("Admin Login")
    username = st.text_input("Username", key="admin_username")
    password = st.text_input("Password", type="password", key="admin_password")
    if st.button("Login", key="admin_login_button"):
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            st.session_state['admin_logged_in'] = True
            st.success("Logged in as admin")
            st.rerun()
        else:
            st.error("Invalid credentials")

def admin_panel():
    if st.button("← Back to Main Menu"):
        st.session_state['admin_logged_in'] = False
        st.rerun()
        
    st.title("Admin Panel")
    task = st.sidebar.selectbox("Select Task", ["User Management", "System Monitoring", "Certificate Management", "Log out"])
    if task == "User Management":
        user_management()
    elif task == "System Monitoring":
        system_monitoring()
    elif task == "Certificate Management":
        certificate_management()
    elif task == "Log out":
        st.session_state['admin_logged_in'] = False
        st.rerun()

def user_management():
    st.subheader("User Management")
    if st.button("← Back"):
        st.rerun()

    db_wrapper = db_con.DBWrapper()
    users = db_wrapper.get_all_users()
    
    # Convert to DataFrame
    df = pd.DataFrame(users, columns=['UID', 'Name', 'Phone Hash', 'Email Hash', 'Amount Invested', 'Date', 'Resale Value', 'Certificate Type'])
    
    # Create column filters
    col1, col2, col3, col4 = st.columns(4)
    filters = {}
    with col1:
        filters['Name'] = st.text_input("Filter Name")
    with col2:
        filters['Amount Invested'] = st.text_input("Filter Amount")
    with col3:
        filters['Date'] = st.text_input("Filter Date")
    with col4:
        filters['Certificate Type'] = st.text_input("Filter Certificate")

    # Apply filters using fuzzy matching
    filtered_df = df.copy()
    for column, search_term in filters.items():
        if search_term:
            if column in ['Amount Invested', 'Resale Value']:
                try:
                    filtered_df = filtered_df[filtered_df[column].astype(str).str.contains(search_term, case=False)]
                except:
                    pass
            else:
                mask = filtered_df[column].apply(lambda x: fuzz.partial_ratio(str(x).lower(), search_term.lower()) > 75)
                filtered_df = filtered_df[mask]

    # Display table
    st.dataframe(filtered_df, use_container_width=True)

    db_wrapper.close()

def display_user_info(user):
    uid = user[0]
    st.markdown(f"### User: {user[1]} (UID: {uid})")
    st.write(f"**Phone Hash:** {user[2]}")
    st.write(f"**Email Hash:** {user[3]}")
    st.write(f"**Amount Invested:** ₹{user[4]}")
    st.write(f"**Date of Investment:** {user[5]}")
    st.write(f"**Resale Value:** ₹{user[6]}")
    st.write(f"**Certificate Type:** {user[7]}")

    # Allow editing each field
    if st.checkbox(f"Edit User {uid}", key=f"edit_{uid}"):
        new_name = st.text_input("Name", value=user[1], key=f"name_{uid}")
        new_amount = st.number_input("Amount Invested", value=user[4], step=500, key=f"amount_{uid}")
        new_resale = st.number_input("Resale Value", value=user[6], key=f"resale_{uid}")
        cert_options = ["Small Card (₹40)", "A4 Sized Certificate (₹80)"]
        cert_index = cert_options.index(user[7]) if user[7] in cert_options else 0
        new_certificate_type = st.selectbox("Certificate Type", cert_options, index=cert_index, key=f"cert_type_{uid}")

        if st.button("Update User", key=f"update_{uid}"):
            db_wrapper = db_con.DBWrapper()
            try:
                # Update user fields
                db_wrapper.update_user_field(uid, 'name', new_name)
                db_wrapper.update_user_field(uid, 'amount_invested', new_amount)
                db_wrapper.update_user_field(uid, 'resale_value', new_resale)
                db_wrapper.update_user_field(uid, 'certificate_type', new_certificate_type)
                st.success("User updated successfully.")
                st.rerun()
            except Exception as e:
                st.error(f"Error updating user: {e}")
            finally:
                db_wrapper.close()

    # Option to delete user
    if st.button(f"Delete User {uid}", key=f"delete_{uid}"):
        confirm_delete = st.checkbox(f"Are you sure you want to delete user {uid}? This action cannot be undone.", key=f"confirm_delete_{uid}")
        if confirm_delete:
            db_wrapper = db_con.DBWrapper()
            try:
                db_wrapper.delete_user(uid)
                st.success("User deleted successfully.")
                st.rerun()
            except Exception as e:
                st.error(f"Error deleting user: {e}")
            finally:
                db_wrapper.close()

def system_monitoring():
    if st.button("← Back"):
        st.rerun()

    st.subheader("System Monitoring")
    
    col1, col2 = st.columns(2)
    
    # CPU and GPU Usage (Bar Chart)
    with col1:
        cpu_percent = psutil.cpu_percent(percpu=True)
        fig_cpu = go.Figure(data=[
            go.Bar(name='CPU Usage', x=[f'Core {i+1}' for i in range(len(cpu_percent))], y=cpu_percent)
        ])
        fig_cpu.update_layout(title='CPU Usage by Core', height=300)
        st.plotly_chart(fig_cpu, use_container_width=True)

    # RAM Usage (Pie Chart)
    with col2:
        ram = psutil.virtual_memory()
        fig_ram = px.pie(
            values=[ram.used, ram.available],
            names=['Used', 'Available'],
            title='RAM Usage'
        )
        fig_ram.update_layout(height=300)
        st.plotly_chart(fig_ram, use_container_width=True)

    # Disk Usage (Pie Chart)
    col3, col4 = st.columns(2)
    with col3:
        disk = psutil.disk_usage('/')
        fig_disk = px.pie(
            values=[disk.used, disk.free],
            names=['Used', 'Free'],
            title='Disk Usage'
        )
        fig_disk.update_layout(height=300)
        st.plotly_chart(fig_disk, use_container_width=True)

def certificate_management():
    if st.button("← Back"):
        st.rerun()

    st.subheader("Certificate Management")
    cert_folder = Path("assets/certs")
    card_folder = Path("assets/certs/cards")

    all_cert_files = list(cert_folder.glob("*.docx")) + list(card_folder.glob("*.docx"))
    
    # Process filenames for search
    processed_names = {
        file: file.stem.lower().replace('_', ' ')
        for file in all_cert_files
    }

    search_query = st.text_input("Search for certificates/cards by name:")
    
    if search_query:
        search_query = search_query.lower()
        # Perform fuzzy search on processed names
        matched_files = process.extract(
            search_query, 
            {file: name for file, name in processed_names.items()},
            scorer=fuzz.partial_ratio,
            limit=50
        )
        files_to_display = [file for file, score in matched_files if score > 75]
    else:
        files_to_display = all_cert_files

    # Display files
    for cert_file in files_to_display:
        st.write(f"**{cert_file.stem}**")
        try:
            with open(cert_file, "rb") as file:
                st.download_button(
                    label=f"Download {cert_file.name}",
                    data=file.read(),
                    file_name=cert_file.name,
                    mime='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                    key=f"download_{cert_file.name}"
                )
        except Exception as e:
            st.error(f"Error reading file {cert_file.name}: {e}")

def display_certificates(cert_files, cert_type, db_wrapper):
    for cert_file in cert_files:
        st.write(f"**{cert_file.name}**")
        uid = extract_uid_from_filename(cert_file.name)

        if cert_file.is_file():
            try:
                with open(cert_file, "rb") as file:
                    file_content = file.read()

                if st.button(f"Download {cert_file.name}", key=f"download_{cert_file.name}"):
                    # Check if it's the first download
                    transactions = db_wrapper.get_transactions(uid)
                    download_transactions = [txn for txn in transactions if txn['type'] == 'certificate_download' and txn['details'] == cert_file.name]

                    if not download_transactions:
                        st.write("**This is the original copy.**")
                        # Log as original copy download
                        db_wrapper.add_transaction(uid, 'certificate_download', 0, f"{cert_file.name} - Original")
                    else:
                        st.write("**This is a duplicate copy.**")
                        # Log as duplicate copy download
                        db_wrapper.add_transaction(uid, 'certificate_download', 0, f"{cert_file.name} - Duplicate")

                    st.download_button(
                        label="Download File",
                        data=file_content,
                        file_name=cert_file.name,
                        mime='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                    )
            except Exception as e:
                st.error(f"Error reading file {cert_file.name}: {e}")
        else:
            st.warning(f"File {cert_file.name} does not exist.")

def extract_uid_from_filename(filename):
    # Remove file extension
    name_without_ext = filename.rsplit('.', 1)[0]
    # Return the name with underscores (unchanged)
    return name_without_ext