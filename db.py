import mysql.connector
import streamlit as st

def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",         
            password="Sedhu.k001@",
            database="cqms"
        )
        return conn
    except mysql.connector.Error as e:
        st.error(f"Database connection error: {e}")
        return None
