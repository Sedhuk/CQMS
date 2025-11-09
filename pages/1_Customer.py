import streamlit as st
from datetime import datetime
from db import get_db_connection




# ✅ Get user details
def get_user_details(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM customer_profile WHERE user_id = %s", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user
def get_user_name(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("select name from user_login where user_id = %s", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user

# ✅ Update user details
def update_user_details(user_id, phone, address):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE customer_profile 
        SET phone = %s, address = %s 
        WHERE user_id = %s
    """, (phone, address, user_id))
    conn.commit()
    conn.close()

def create_ticket(customer_id, heading, description, priority):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO support_ticket (customer_id,subject,description, priority, status, ticket_raised_on)
        VALUES (%s, %s, %s, %s, 'open', %s)
    """, (customer_id,heading, description, priority, datetime.now()))
    conn.commit()
    conn.close()


def get_user_tickets(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT ticket_id, subject, priority, status, ticket_raised_on,ticket_closed_on
        FROM support_ticket
        WHERE customer_id = %s
        ORDER BY ticket_raised_on DESC
    """, (user_id,))
    tickets = cursor.fetchall()
    conn.close()
    return tickets

# ✅ Secure page access
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.error("Please login first.")
    st.stop()
user_id = st.session_state.user_id
profile = get_user_name(user_id)
user_name = profile["name"] if profile else "User"

st.set_page_config(page_title= "customer Dashboard", page_icon="🛠️")
col1, col2 = st.columns([7, 2])  # Adjust ratio to control spacing
with col1:
    st.title("🛠️Welcome " + str(user_name))
with col2:
    st.markdown("<br>", unsafe_allow_html=True)  # small vertical alignment fix
    if st.button("Logout", key="logout_btn"):
        st.session_state.login = False
        st.session_state.role = None
        st.switch_page("login.py")
        
customer_id = ''
# -------------------- TABS --------------------
tab1, tab2,tab3,tab4 = st.tabs(["👤 My Profile", "🆕 Create New Ticket","📋 My Tickets","🔒 Close Tickets"])

# -------------------- TAB 1: VIEW / UPDATE PROFILE --------------------
with tab1:
    profile = get_user_details(user_id)

    if not profile:
        st.warning("⚠️ No profile data found for this user.")
    else:
        st.subheader("Your Profile Details")

        with st.form("profile_form"):
            st.write("You can update your contact details below:")
            st.text_input("Name", value=profile["company_name"], disabled=True)
            phone = st.text_input("Phone", value=profile["phone"])
            address = st.text_area("Address", value=profile["address"])
            customer_id = profile["customer_id"]

            update_btn = st.form_submit_button("💾 Update Profile")

            if update_btn:
                update_user_details(user_id, phone, address)
                st.success("✅ Profile updated successfully!")

# -------------------- TAB 2: CREATE NEW TICKET --------------------
with tab2:
    st.subheader("Create New Support Ticket")
    with st.form("ticket_form"):
        query_heading = st.text_input("Query Heading")
        query_description = st.text_area("Query Description")
        priority = st.selectbox("Priority", ["Low", "Medium", "High"])

        submit_ticket = st.form_submit_button("🚀 Submit Ticket")

        if submit_ticket:
            create_ticket(customer_id, query_heading, query_description, priority)
            st.success("✅ Your support ticket has been created successfully!")
            query_description = ''
            query_heading = ''
            priority = 'Low'

with tab3:
    st.subheader("📋 My Submitted Tickets")
    tickets = get_user_tickets(customer_id)

    if not tickets:
        st.info("No tickets found. You haven’t raised any support queries yet.")
    else:
        # Add some CSS styling for better UI
        st.markdown("""
        <style>
        .stDataFrame { border: 2px solid #4A90E2; border-radius: 10px; }
        </style>
        """, unsafe_allow_html=True)

        # Convert date to readable format
        for t in tickets:
            t["ticket_raised_on"] = t["ticket_raised_on"].strftime("%Y-%m-%d %H:%M:%S")
            if t["ticket_closed_on"] not in (None, '', 'null'):
                t["ticket_closed_on"] = t["ticket_closed_on"].strftime("%Y-%m-%d %H:%M:%S")
            else:
                  t["ticket_closed_on"] = ''


        st.dataframe(
            tickets,
            use_container_width=True,
            hide_index=True
        )

with tab4:
    if not tickets:
        st.info("No tickets found. You haven’t raised any support queries yet.")
    else:
        # CSS Styling for cards + status colors
        st.markdown("""
        <style>
        .expander-header {
            font-weight: bold;
            font-size: 16px;
            color: white;
            padding: 8px 12px;
            border-radius: 8px;
            margin-top: 10px;
            margin-bottom: 4px;
        }
        .status-open { background-color: #FFA500; }        /* Orange */
        .status-inprogress { background-color: #2196F3; }  /* Blue */
        .status-closed { background-color: #4CAF50; }      /* Green */
        </style>
        """, unsafe_allow_html=True)

        for ticket in tickets:
            # Pick color class based on ticket status
            status = ticket["status"].lower()
            if status == "open":
                color_class = "status-open"
            elif status == "in progress":
                color_class = "status-inprogress"
            else:
                color_class = "status-closed"

            # Colored header rendered above expander
            st.markdown(f"""
                <div class="expander-header {color_class}">
                    🎫 {ticket['subject']} — [{ticket['status'].upper()}]
                </div>
            """, unsafe_allow_html=True)

            with st.expander("View Details"):
                st.markdown(f"**Ticket ID:** {ticket['ticket_id']}")
                st.markdown(f"**Priority:** {ticket['priority']}")

                created_at = ticket["ticket_raised_on"]
                if hasattr(created_at, "strftime"):
                    created_at = created_at.strftime("%Y-%m-%d %H:%M:%S")
                st.markdown(f"**Created At:** {created_at}")
                st.markdown("---")

                # Fetch details from DB
                conn = get_db_connection()
                cursor = conn.cursor(dictionary=True)
                cursor.execute("""
                    SELECT description, comments, status, customer_review, review_stars 
                    FROM support_ticket 
                    WHERE ticket_id = %s
                """, (ticket["ticket_id"],))
                details = cursor.fetchone()
                conn.close()

                st.markdown(f"**Description:** {details['description']}")
                st.markdown(f"**Comments:** {details['comments'] or 'No comments yet'}")
                st.markdown("---")

                # Actions based on status
                if details["status"] == "Open":
                    if st.button(f"🛑 Close Ticket #{ticket['ticket_id']}"):
                        conn = get_db_connection()
                        cursor = conn.cursor()
                        cursor.execute("""
                            UPDATE support_ticket 
                            SET status = 'Closed', ticket_closed_on = NOW()
                            WHERE ticket_id = %s
                        """, (ticket["ticket_id"],))
                        conn.commit()
                        conn.close()
                        st.success(f"✅ Ticket #{ticket['ticket_id']} closed successfully!")
                        st.rerun()

                elif details["status"] == "Closed":
                    if details["customer_review"] is None:
                        st.info("📝 This ticket is closed. Please share your feedback.")
                        with st.form(f"review_form_{ticket['ticket_id']}"):
                            review_text = st.text_area("Your Review")
                            review_stars = st.slider("Rating (1 = poor, 5 = excellent)", 1, 5, 5)
                            submit_review = st.form_submit_button("💬 Submit Review")
                            Reopen = st.form_submit_button("Reopen")

                            if submit_review:
                                conn = get_db_connection()
                                cursor = conn.cursor()
                                cursor.execute("""
                                    UPDATE support_ticket
                                    SET customer_review = %s, review_stars = %s
                                    WHERE ticket_id = %s
                                """, (review_text, review_stars, ticket["ticket_id"]))
                                conn.commit()
                                conn.close()
                                st.success("⭐ Thank you for your feedback!")
                                st.rerun()
                    else:
                        st.markdown(f"**Customer Review:** {details['customer_review']}")
                        stars = details['review_stars'] if details['review_stars'] else 0
                        if stars > 0:
                            st.markdown(f"**Stars:** {'⭐' * stars}")
                        else:
                            st.markdown("**Stars:** No rating provided yet.")
