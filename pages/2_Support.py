import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime
from db import get_db_connection
import streamlit as st


# ✅ Fetch all open and closed tickets
def get_all_tickets():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT 
            t.ticket_id,
            c.company_name,
            c.phone,
            t.subject,
            t.description,
            t.priority,
            t.status,
            t.ticket_raised_on,
            t.ticket_closed_on,
            t.comments,
            t.customer_review,
            t.review_stars
        FROM support_ticket t
        JOIN customer_profile c ON t.customer_id = c.customer_id
        ORDER BY t.ticket_raised_on DESC
    """)
    tickets = cursor.fetchall()
    conn.close()
    return tickets




def update_ticket_status(ticket_id, new_status):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "UPDATE support_ticket SET status = %s, ticket_closed_on = NOW() WHERE ticket_id = %s"
    cursor.execute(query, (new_status, ticket_id))
    conn.commit()
    conn.close()
    st.success(f"✅ Ticket #{ticket_id} updated to {new_status}")


def update_ticket_comment(ticket_id, comment):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE support_ticket SET comments = %s WHERE ticket_id = %s",
        (comment, ticket_id)
    )
    conn.commit()
    conn.close()


# ✅ Analytics data
def get_ticket_analytics():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
       SELECT 
    t.ticket_id,
    t.subject,
    t.priority,
    t.status,
    t.ticket_raised_on,
    t.ticket_closed_on,
    TIMESTAMPDIFF(HOUR, t.ticket_raised_on, t.ticket_closed_on) AS resolution_hours,
    u.name AS name
FROM support_ticket t
INNER JOIN customer_profile c 
    ON t.customer_id = c.customer_id
INNER JOIN user_login u 
    ON c.user_id = u.user_id;

    """)
    data = cursor.fetchall()
    conn.close()
    return pd.DataFrame(data)

def get_user_name(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("select name from user_login where user_id = %s", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user

user_id = st.session_state.user_id
profile = get_user_name(user_id)
user_name = profile["name"] if profile else "User"

st.set_page_config(page_title="Support Dashboard", page_icon="🛠️")
col1, col2 = st.columns([7, 2])  # Adjust ratio to control spacing
with col1:
    st.title("🛠️Welcome " + str(user_name))
with col2:
    st.markdown("<br>", unsafe_allow_html=True)  # small vertical alignment fix
    if st.button("Logout", key="logout_btn"):
        st.session_state.login = False
        st.session_state.role = None
        st.switch_page("login.py")


tab1, tab2 = st.tabs(["📋 Ticket Management", "📊 Analytics"])

# ✅ Inject CSS styling
st.markdown("""
<style>
/* Table border styling */
.ticket-table {
    border: 2px solid #4A90E2;
    border-radius: 8px;
    padding: 10px;
    margin-bottom: 20px;
}

/* Expander border */
.streamlit-expanderHeader {
    font-size: 18px !important;
    font-weight: bold !important;
    color: #1E88E5 !important;
}
.streamlit-expander {
    border: 2px solid #FF9800 !important;
    border-radius: 8px !important;
}

/* Action buttons inline */
.action-buttons button {
    margin-right: 8px !important;
}
</style>
""", unsafe_allow_html=True)




# ==============================
# TAB 1 - Ticket Management
# ==============================
with tab1:
    st.subheader("📋 All Customer Tickets")

    # Inject CSS for colored headers
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

    tickets = get_all_tickets()

    if not tickets:
        st.info("No tickets found in the system yet.")
    else:
        for ticket in tickets:
            # Determine color based on ticket status
            status = ticket["status"].lower()
            if status == "open":
                color_class = "status-open"
            elif status == "in progress":
                color_class = "status-inprogress"
            else:
                color_class = "status-closed"

            # Render colored header before expander
            st.markdown(f"""
                <div class="expander-header {color_class}">
                    🎫 Ticket #{ticket['ticket_id']} — {ticket['subject']} [{ticket['status'].upper()}]
                </div>
            """, unsafe_allow_html=True)

            with st.expander("View Details"):
                st.markdown(f"**Customer:** {ticket['company_name']}")
                st.markdown(f"**Phone:** {ticket['phone']}")
                st.markdown(f"**Priority:** {ticket['priority']}")
                st.markdown(f"**Description:** {ticket['description']}")

                if ticket['status'] == 'Closed':
                    st.markdown(f"**Customer Review:** {ticket['customer_review'] or 'No review yet'}")

                st.markdown(f"**Created At:** {ticket['ticket_raised_on']}")
                if ticket["ticket_closed_on"] and ticket['status'] == 'Closed':
                    st.markdown(f"**Closed At:** {ticket['ticket_closed_on']}")

                # Comment Update Section
                with st.form(f"comment_form_{ticket['ticket_id']}"):
                    new_comment = st.text_area("💬 Add / Update Comment", value=ticket['comments'] or "")
                    submit_comment = st.form_submit_button(
                        "💾 Save Comment" if not ticket["comments"] else "💾 Update Comment"
                    )

                    if submit_comment:
                        update_ticket_comment(ticket["ticket_id"], new_comment)
                        st.success("✅ Comment updated successfully!")
                        st.rerun()

                # Action Buttons: Close / In Progress
                if ticket["status"].lower() in ["open", "in progress"]:
                    col3, col4 = st.columns([7, 2])
                    with col3:
                        if st.button(f"🛑 Close Ticket #{ticket['ticket_id']}", key=f"close_{ticket['ticket_id']}"):
                            update_ticket_status(ticket["ticket_id"], "Closed")
                            st.success(f"✅ Ticket #{ticket['ticket_id']} closed successfully!")
                            st.rerun()

                    with col4:
                        if st.button("🚧 In Progress", key=f"in_progress_{ticket['ticket_id']}"):
                            update_ticket_status(ticket["ticket_id"], "In Progress")
                            st.success(f"✅ Ticket #{ticket['ticket_id']} status changed successfully!")
                            st.rerun()
                else:
                    st.info("✅ This ticket is already closed.")

                # Show Customer Review if Exists
                if ticket["customer_review"]:
                    st.markdown("---")
                    st.markdown(f"**Customer Review:** {ticket['customer_review']}")
                    if ticket["review_stars"]:
                        stars = int(ticket["review_stars"])
                        st.markdown(f"**Rating:** {'⭐' * stars}")

# ==============================
# TAB 2 - Analytics
# ==============================
with tab2:
    st.subheader("📊 Support Analytics Dashboard")

    df_analytics = get_ticket_analytics()

    if df_analytics.empty:
        st.info("No data available yet for analytics.")
    else:
        # ---- SERVICE EFFICIENCY ----
        st.markdown("### ⚡ Service Efficiency (Average Resolution Time in Hours)")
        df_closed = df_analytics[df_analytics["status"].str.lower() == "closed"]

        if not df_closed.empty:
            avg_resolution = df_closed["resolution_hours"].mean()
            st.metric(label="Average Resolution Time", value=f"{avg_resolution:.1f} hours")

            plt.figure(figsize=(7, 4))
            plt.hist(df_closed["resolution_hours"].dropna(), bins=10)
            plt.xlabel("Resolution Time (hours)")
            plt.ylabel("Number of Tickets")
            plt.title("Distribution of Ticket Resolution Times")
            st.pyplot(plt)
        else:
            st.info("No closed tickets yet to calculate resolution times.")

        # ---- SUPPORT LOAD MONITORING ----
        st.markdown("### 🧭 Support Load Monitoring (By Priority)")
        load_data = df_analytics.groupby("priority").size().reset_index(name="Count")

        plt.figure(figsize=(6, 4))
        plt.bar(load_data["priority"], load_data["Count"])
        plt.xlabel("Priority")
        plt.ylabel("Number of Tickets")
        plt.title("Ticket Load by Priority")
        st.pyplot(plt)

        # ---- STATUS DISTRIBUTION ----
        st.markdown("### 📈 Ticket Status Overview")
        status_counts = df_analytics["status"].value_counts().reset_index()
        status_counts.columns = ["Status", "Count"]

        plt.figure(figsize=(6, 4))
        plt.bar(status_counts["Status"], status_counts["Count"], color=["#FFA500", "#2196F3", "#4CAF50"])
        plt.xlabel("Ticket Status")
        plt.ylabel("Number of Tickets")
        plt.title("Open vs In Progress vs Closed Tickets")
        st.pyplot(plt)

        # ---- PRIORITY VS STATUS ----
        st.markdown("### 🎯 Ticket Distribution by Priority & Status")
        pivot_priority_status = (
            df_analytics.groupby(["priority", "status"])
            .size()
            .reset_index(name="Count")
        )

        pivot_table = pivot_priority_status.pivot(index="priority", columns="status", values="Count").fillna(0)
        st.dataframe(pivot_table, use_container_width=True)

        plt.figure(figsize=(7, 4))
        pivot_priority_status.pivot(index="priority", columns="status", values="Count").plot(kind="bar", figsize=(7, 4))
        plt.title("Priority vs Status Overview")
        plt.xlabel("Priority")
        plt.ylabel("Ticket Count")
        plt.xticks(rotation=0)
        st.pyplot(plt)

        # ---- USER-WISE STATUS COUNT ----
        st.markdown("### 👥 Tickets by User and Status")
        user_status = (
            df_analytics.groupby(["name", "status"])
            .size()
            .reset_index(name="Count")
        )

        st.dataframe(user_status, use_container_width=True)

        plt.figure(figsize=(8, 4))
        for status in user_status["status"].unique():
            subset = user_status[user_status["status"] == status]
            plt.bar(subset["name"], subset["Count"], label=status)
        plt.title("Ticket Count by User and Status")
        plt.xlabel("Customer / User")
        plt.ylabel("Number of Tickets")
        plt.legend(title="Status")
        plt.xticks(rotation=45, ha="right")
        st.pyplot(plt)

        # ---- MOST COMMON QUERY TYPES ----
        st.markdown("### 💬 Most Common Query Topics")
        top_subjects = df_analytics["subject"].value_counts().head(5)
        st.bar_chart(top_subjects)
