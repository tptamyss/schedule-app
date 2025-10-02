import streamlit as st
from datetime import datetime, date, time
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import gspread
from google.oauth2.service_account import Credentials

# Initialize Google Sheets connection
@st.cache_resource
def init_gsheet():
    scope = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    
    try:
        credentials = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=scope
        )
        
        client = gspread.authorize(credentials)
        
        # Use the exact sheet name or URL
        sheet = client.open("Interview Scheduler").sheet1
        
        # Initialize headers if empty
        if sheet.row_count == 0 or sheet.cell(1, 1).value is None:
            sheet.append_row(['id', 'slot_date', 'start_time', 'end_time', 'is_booked', 'candidate_name', 'candidate_email', 'created_at'])
        
        return sheet
    except Exception as e:
        st.error(f"Error details: {str(e)}")
        raise

# Admin credentials
ADMIN_EMAIL = "buvjapanesecultureclub@gmail.com"
ADMIN_PASSWORD = "secretsociety"

# Email config
GMAIL_USER = "buvjapanesecultureclub@gmail.com"
GMAIL_APP_PASSWORD = "qskc sfyi kihk ygbt"

def add_time_slot(slot_date, start_time, end_time):
    sheet = init_gsheet()
    all_records = sheet.get_all_records()
    new_id = len(all_records) + 1
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sheet.append_row([new_id, slot_date, start_time, end_time, 0, '', '', created_at])

def get_available_slots():
    sheet = init_gsheet()
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    if len(df) > 0:
        df = df[df['is_booked'] == 0].sort_values(['slot_date', 'start_time'])
    return df

def get_all_slots():
    sheet = init_gsheet()
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    if len(df) > 0:
        df = df.sort_values(['slot_date', 'start_time'])
    return df

def book_slot(slot_id, candidate_name, candidate_email):
    sheet = init_gsheet()
    all_records = sheet.get_all_records()
    for idx, record in enumerate(all_records, start=2):  # Start at 2 because row 1 is headers
        if record['id'] == slot_id:
            sheet.update_cell(idx, 5, 1)  # is_booked column
            sheet.update_cell(idx, 6, candidate_name)
            sheet.update_cell(idx, 7, candidate_email)
            break

def delete_slot(slot_id):
    sheet = init_gsheet()
    all_records = sheet.get_all_records()
    for idx, record in enumerate(all_records, start=2):
        if record['id'] == slot_id:
            sheet.delete_rows(idx)
            break

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
Gửi bạn {candidate_name},

Sau đây là một số thông tin về buổi phỏng vấn
- Hình thức : Phỏng vấn trực tiếp
- Địa điểm : Sảnh nghỉ trước phòng D2-11- BUV Campus
- Thời gian:
📅 Ngày: {slot_date}
🕐 Vào lúc: {start_time} - {end_time}

Vì không gian khu vực khá rộng
BJC mong muốn bạn có thể nắm chắc các thông tin trên 
để buổi phỏng vấn có thể diễn thành công và tốt đẹp.

Chúng mình rất mong chờ được gặp bạn ở buổi phỏng
vấn sắp tới. Nếu có thắc mắc hay bất kì điều chỉnh nào
hãy gửi email về địa chỉ này.
Thân gửi,
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
        return False, "Thank you for booking with us"
    
# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_type' not in st.session_state:
    st.session_state.user_type = None

# Initialize Google Sheets
try:
    init_gsheet()
except Exception as e:
    st.error(f"Failed to connect to Google Sheets: {e}")

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
                        all_slots_df = get_all_slots()
                        slot_details = all_slots_df[all_slots_df['id'] == st.session_state.selected_slot]
                        
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