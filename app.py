import streamlit as st
import sqlite3
from datetime import datetime, date, time
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

# Initialize database
def init_db():
    conn = sqlite3.connect('interview_scheduler.db')
    c = conn.cursor()
    
    # Create time slots table
    c.execute('''CREATE TABLE IF NOT EXISTS time_slots
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  slot_date TEXT NOT NULL,
                  start_time TEXT NOT NULL,
                  end_time TEXT NOT NULL,
                  is_booked INTEGER DEFAULT 0,
                  candidate_name TEXT,
                  candidate_email TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    conn.commit()
    conn.close()

# Admin credentials
ADMIN_EMAIL = st.secrets.get("ADMIN_EMAIL", "admin@admin.com")
ADMIN_PASSWORD = st.secrets.get("ADMIN_PASSWORD", "admin123")

# Email config
GMAIL_USER = st.secrets.get("GMAIL_USER", "")
GMAIL_APP_PASSWORD = st.secrets.get("GMAIL_APP_PASSWORD", "")
# Database functions
def add_time_slot(slot_date, start_time, end_time):
    conn = sqlite3.connect('interview_scheduler.db')
    c = conn.cursor()
    c.execute("INSERT INTO time_slots (slot_date, start_time, end_time) VALUES (?, ?, ?)",
              (slot_date, start_time, end_time))
    conn.commit()
    conn.close()

def get_available_slots():
    conn = sqlite3.connect('interview_scheduler.db')
    df = pd.read_sql_query("SELECT * FROM time_slots WHERE is_booked = 0 ORDER BY slot_date, start_time", conn)
    conn.close()
    return df

def get_all_slots():
    conn = sqlite3.connect('interview_scheduler.db')
    df = pd.read_sql_query("SELECT * FROM time_slots ORDER BY slot_date, start_time", conn)
    conn.close()
    return df

def book_slot(slot_id, candidate_name, candidate_email):
    conn = sqlite3.connect('interview_scheduler.db')
    c = conn.cursor()
    c.execute("UPDATE time_slots SET is_booked = 1, candidate_name = ?, candidate_email = ? WHERE id = ?",
              (candidate_name, candidate_email, slot_id))
    conn.commit()
    conn.close()

def delete_slot(slot_id):
    conn = sqlite3.connect('interview_scheduler.db')
    c = conn.cursor()
    c.execute("DELETE FROM time_slots WHERE id = ?", (slot_id,))
    conn.commit()
    conn.close()

def send_confirmation_email(candidate_name, candidate_email, slot_date, start_time, end_time):
    """Send confirmation email to candidate"""
    
    # Check if email is configured
    if not GMAIL_USER or not GMAIL_APP_PASSWORD:
        return False, "Email not configured. Please set up Gmail credentials in Email Settings."
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = GMAIL_USER
        msg['To'] = candidate_email
        msg['Subject'] = "Interview Confirmation - Your Slot is Booked!"
        
        # Email body
        body = f"""
Dear {candidate_name},

Thank you for scheduling an interview with us!

Your interview has been successfully booked for:

📅 Date: {slot_date}
🕐 Time: {start_time} - {end_time}

Please make sure to:
- Join the meeting 5 minutes early
- Have a stable internet connection

If you need to reschedule or have any questions, please contact us.

We look forward to meeting you!

Best regards,
BUV Japanese Culture Club
"""
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email with detailed error catching
        server = smtplib.SMTP('smtp.gmail.com', 587, timeout=10)
        server.set_debuglevel(0)  # Set to 1 for verbose debugging
        server.starttls()
        server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        return True, "You will receive a confirmation email soon."
    
    except smtplib.SMTPAuthenticationError:
        return False, "Authentication failed. Please check your Gmail address and app password."
    except smtplib.SMTPException as e:
        return False, f"SMTP error: {str(e)}"
    except Exception as e:
        return False, f"Error: {str(e)}"
    
# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_type' not in st.session_state:
    st.session_state.user_type = None

# Initialize database
init_db()

# Main app
st.title("📅 BUV Japanese Culture Club Interview Schedule")

# Login/Role selection page
if not st.session_state.logged_in:
    st.subheader("Welcome! You are?")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("I'm an Interviewer", use_container_width=True):
            st.session_state.user_type = "interviewer"
    
    with col2:
        if st.button("I'm a Candidate", use_container_width=True):
            st.session_state.user_type = "candidate"
            st.session_state.logged_in = True
            st.rerun()
    
    # Show login form for interviewer
    if st.session_state.user_type == "interviewer":
        st.markdown("---")
        st.subheader("Interviewer Login")
        
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        
        if st.button("Login"):
            if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
                st.session_state.logged_in = True
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid credentials. Please try again.")

elif st.session_state.logged_in and st.session_state.user_type == "interviewer":
    st.sidebar.success(f"Logged in as: {ADMIN_EMAIL}")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.user_type = None
        st.rerun()
    
    st.header("Admin Dashboard")
    
    # Tabs for different sections
    tab1, tab2, = st.tabs(["➕ Add Time Slot", "📋 View All Bookings"])
    
    with tab1:
        st.subheader("Create New Time Slot")
        
        col1, col2 = st.columns(2)
        
        with col1:
            slot_date = st.date_input("Select Date", min_value=date.today())
        
        with col2:
            start_time = st.time_input("Start Time")
        
        end_time = st.time_input("End Time")
        
        if st.button("Add Time Slot", type="primary"):
            if end_time <= start_time:
                st.error("End time must be after start time!")
            else:
                add_time_slot(
                    slot_date.strftime("%Y-%m-%d"),
                    start_time.strftime("%H:%M"),
                    end_time.strftime("%H:%M")
                )
                st.success(f"✅ Time slot added: {slot_date} from {start_time} to {end_time}")
                st.rerun()
    
    with tab2:
        st.subheader("All Interview Slots")
        
        all_slots = get_all_slots()
        
        if len(all_slots) == 0:
            st.info("No time slots created yet.")
        else:
            for idx, row in all_slots.iterrows():
                with st.container():
                    col1, col2, col3 = st.columns([3, 2, 1])
                    
                    with col1:
                        status = "🔴 Booked" if row['is_booked'] else "🟢 Available"
                        st.write(f"**{row['slot_date']}** | {row['start_time']} - {row['end_time']} | {status}")
                    
                    with col2:
                        if row['is_booked']:
                            st.write(f"👤 {row['candidate_name']}")
                            st.write(f"📧 {row['candidate_email']}")
                    
                    with col3:
                        if st.button("🗑️", key=f"delete_{row['id']}"):
                            delete_slot(row['id'])
                            st.rerun()
                    
                    st.divider()

# Candidate Dashboard
elif st.session_state.logged_in and st.session_state.user_type == "candidate":
    if st.sidebar.button("Back to Home"):
        st.session_state.logged_in = False
        st.session_state.user_type = None
        st.rerun()
    
    st.header("Available Interview Slots")
    st.write("Select a time slot and enter your details to book an interview.")
    
    available_slots = get_available_slots()
    
    if len(available_slots) == 0:
        st.info("No available time slots at the moment. Please check back later.")
    else:
        # Group by date
        dates = available_slots['slot_date'].unique()
        
        for slot_date in dates:
            st.subheader(f"📅 {slot_date}")
            
            date_slots = available_slots[available_slots['slot_date'] == slot_date]
            
            cols = st.columns(3)
            
            for idx, row in date_slots.iterrows():
                col_idx = idx % 3
                
                with cols[col_idx]:
                    button_label = f"{row['start_time']} - {row['end_time']}"
                    
                    if st.button(button_label, key=f"slot_{row['id']}", use_container_width=True):
                        st.session_state.selected_slot = row['id']
                        st.session_state.selected_slot_info = f"{row['slot_date']} from {row['start_time']} to {row['end_time']}"
            
            st.markdown("---")
        
        # Booking form
        if 'selected_slot' in st.session_state:
            st.subheader("Complete Your Booking")
            st.info(f"Selected slot: {st.session_state.selected_slot_info}")
            
            candidate_name = st.text_input("Your Name*")
            candidate_email = st.text_input("Your Email*")
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                if st.button("Confirm Booking", type="primary"):
                    if candidate_name and candidate_email:
                        # Get slot details before booking
                        conn = sqlite3.connect('interview_scheduler.db')
                        slot_details = pd.read_sql_query(f"SELECT * FROM time_slots WHERE id = {st.session_state.selected_slot}", conn)
                        conn.close()
                        
                        if len(slot_details) > 0:
                            slot = slot_details.iloc[0]
                            
                            # Book the slot
                            book_slot(st.session_state.selected_slot, candidate_name, candidate_email)
                            
                            # Send confirmation email
                            email_success, email_message = send_confirmation_email(
                                candidate_name,
                                candidate_email,
                                slot['slot_date'],
                                slot['start_time'],
                                slot['end_time']
                            )
                            
                            st.success(f"✅ Interview booked successfully!")
                            st.balloons()
                            st.info(f"**Confirmation Details:**\n\n"
                                    f"📅 Date & Time: {st.session_state.selected_slot_info}\n\n"
                                    f"👤 Name: {candidate_name}\n\n"
                                    f"📧 Email: {candidate_email}")
                            
                            # Show email status
                            if email_success:
                                st.success("📧 " + email_message)
                            else:
                                st.warning("⚠️ Booking confirmed, but email notification failed: " + email_message)
                            
                            # Clear selection
                            del st.session_state.selected_slot
                            del st.session_state.selected_slot_info
                        else:
                            st.error("Slot not found. Please try again.")
                    else:
                        st.error("Please fill in all required fields.")
            
            with col2:
                if st.button("Cancel"):
                    del st.session_state.selected_slot
                    del st.session_state.selected_slot_info
                    st.rerun()