import streamlit as st
from db import get_db_connection
import hashlib

st.set_page_config(page_title="CQMS Login", page_icon="🔐")

st.subheader("Support Center Login")

email = st.text_input("Email")
password = st.text_input("Password", type="password")

role = st.selectbox("Role", ("Customer", "Support"))

if st.button("Login"):
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    conn = get_db_connection()

    if conn:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT * FROM user_login
            WHERE email = %s AND password_hash = %s AND role = %s AND status = 'active'
        """
        cursor.execute(query, (email, hashed_password, role))
        user = cursor.fetchone()

        if user:
            st.success("✅ Login successful!")
            st.session_state.logged_in = True
            st.session_state.user_id = user["user_id"]
            st.session_state.role = user["role"]

            if role == "Customer":
                st.switch_page("pages/1_Customer.py")
            elif role == "Support":
                st.switch_page("pages/2_Support.py")
        else:
            st.error("❌ Invalid login details")

        cursor.close()
        conn.close()
