import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, date
import plotly.express as px
import plotly.graph_objects as go
import os

# Page configuration
st.set_page_config(
    page_title="Sales Incentive Calculator",
    page_icon="💰",
    layout="wide"
)

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user' not in st.session_state:
    st.session_state.user = None
if 'current_page' not in st.session_state:
    st.session_state.current_page = "Dashboard"

def init_database():
    """Initialize database with tables and sample data"""
    try:
        # Ensure instance directory exists
        os.makedirs('instance', exist_ok=True)
        
        conn = sqlite3.connect('instance/sales_incentive.db')
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username VARCHAR(80) UNIQUE NOT NULL,
                email VARCHAR(120) UNIQUE NOT NULL,
                password_hash VARCHAR(128),
                role VARCHAR(20) DEFAULT 'sales_rep',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sale (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                customer_name VARCHAR(100) NOT NULL,
                product_name VARCHAR(100) NOT NULL,
                amount DECIMAL(10,2) NOT NULL,
                commission_amount DECIMAL(10,2) NOT NULL,
                sale_date DATE NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES user (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS commission_rule (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_name VARCHAR(100) NOT NULL,
                commission_rate DECIMAL(5,2) NOT NULL,
                min_amount DECIMAL(10,2) DEFAULT 0,
                max_amount DECIMAL(10,2),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Insert sample users if they don't exist
        users = [
            ('admin', 'admin@example.com', 'admin123', 'admin'),
            ('salesrep', 'salesrep@example.com', 'sales123', 'sales_rep'),
            ('demo', 'demo@example.com', 'demo123', 'sales_rep'),
            ('manager', 'manager@example.com', 'manager123', 'admin')
        ]
        
        for username, email, password, role in users:
            cursor.execute('''
                INSERT OR IGNORE INTO user (username, email, password_hash, role)
                VALUES (?, ?, ?, ?)
            ''', (username, email, password, role))
        
        # Insert sample sales data
        sales_data = [
    (1, 'Nestle India', 'Cloud Analytics Suite', 5200.00, 520.00, '2024-01-15'),
    (2, 'PepsiCo Beverages', 'ERP Subscription', 7600.00, 608.00, '2024-01-17'),
    (3, 'Samsung Electronics', 'IoT Device Package', 11200.00, 1344.00, '2024-01-20'),
    (3, 'ICICI Bank', 'Cybersecurity Service', 4500.00, 360.00, '2024-01-22'),
    (4, 'Nike Sports India', 'E-Commerce Integration', 9800.00, 980.00, '2024-01-25'),
    (1, 'Apple Inc.', 'Cloud Storage Solution', 12500.00, 1500.00, '2024-01-27'),
    (2, 'Sony Pictures', 'AI Marketing Tool', 8800.00, 704.00, '2024-01-28'),
    (4, 'Deloitte Consulting', 'Enterprise SaaS Platform', 15800.00, 1896.00, '2024-01-30')
]

        
        for user_id, customer, product, amount, commission, sale_date in sales_data:
            cursor.execute('''
                INSERT OR IGNORE INTO sale (user_id, customer_name, product_name, amount, commission_amount, sale_date)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, customer, product, amount, commission, sale_date))
        
        # Insert commission rules
        commission_rules = [
            ('Premium Package', 10.00, 0, None),
            ('Standard Package', 8.00, 0, None),
            ('Basic Package', 5.00, 0, None),
            ('Enterprise Solution', 12.00, 10000, None)
        ]
        
        for product, rate, min_amt, max_amt in commission_rules:
            cursor.execute('''
                INSERT OR IGNORE INTO commission_rule (product_name, commission_rate, min_amount, max_amount)
                VALUES (?, ?, ?, ?)
            ''', (product, rate, min_amt, max_amt))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        st.error(f"Database initialization error: {e}")
        return False

def get_db_connection():
    """Get database connection"""
    try:
        conn = sqlite3.connect('instance/sales_incentive.db')
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        st.error(f"Database connection error: {e}")
        return None

def authenticate_user(username, password):
    """Authenticate user"""
    try:
        conn = get_db_connection()
        if not conn:
            return None
        
        user = conn.execute('''
            SELECT * FROM user WHERE username = ? AND password_hash = ?
        ''', (username, password)).fetchone()
        
        conn.close()
        
        if user:
            return dict(user)
        return None
        
    except Exception as e:
        st.error(f"Authentication error: {e}")
        return None

def get_sales_data(user_id=None):
    """Get sales data, optionally filtered by user"""
    try:
        conn = get_db_connection()
        if not conn:
            return []
        
        if user_id:
            sales = conn.execute('''
                SELECT s.*, u.username as salesperson 
                FROM sale s 
                JOIN user u ON s.user_id = u.id
                WHERE s.user_id = ?
                ORDER BY s.sale_date DESC
            ''', (user_id,)).fetchall()
        else:
            sales = conn.execute('''
                SELECT s.*, u.username as salesperson 
                FROM sale s 
                JOIN user u ON s.user_id = u.id
                ORDER BY s.sale_date DESC
            ''').fetchall()
        
        conn.close()
        return [dict(sale) for sale in sales]
    except Exception as e:
        st.error(f"Error fetching sales data: {e}")
        return []

def get_sales_stats(user_id=None):
    """Get sales statistics"""
    try:
        conn = get_db_connection()
        if not conn:
            return {}
        
        if user_id:
            stats = conn.execute('''
                SELECT 
                    COUNT(*) as total_sales,
                    COALESCE(SUM(amount), 0) as total_amount,
                    COALESCE(SUM(commission_amount), 0) as total_commission,
                    COALESCE(AVG(amount), 0) as average_sale
                FROM sale WHERE user_id = ?
            ''', (user_id,)).fetchone()
        else:
            stats = conn.execute('''
                SELECT 
                    COUNT(*) as total_sales,
                    COALESCE(SUM(amount), 0) as total_amount,
                    COALESCE(SUM(commission_amount), 0) as total_commission,
                    COALESCE(AVG(amount), 0) as average_sale
                FROM sale
            ''').fetchone()
        
        conn.close()
        return dict(stats) if stats else {}
    except Exception as e:
        st.error(f"Error fetching statistics: {e}")
        return {}

def get_commission_rules():
    """Get all commission rules"""
    try:
        conn = get_db_connection()
        if not conn:
            return []
        
        rules = conn.execute('''
            SELECT * FROM commission_rule ORDER BY product_name
        ''').fetchall()
        
        conn.close()
        return [dict(rule) for rule in rules]
    except Exception as e:
        st.error(f"Error fetching commission rules: {e}")
        return []

def add_commission_rule(product_name, commission_rate, min_amount, max_amount):
    """Add or update commission rule"""
    try:
        conn = get_db_connection()
        if not conn:
            return False
        
        # Check if rule exists
        existing = conn.execute('''
            SELECT id FROM commission_rule WHERE product_name = ?
        ''', (product_name,)).fetchone()
        
        if existing:
            # Update existing rule
            conn.execute('''
                UPDATE commission_rule 
                SET commission_rate = ?, min_amount = ?, max_amount = ?
                WHERE product_name = ?
            ''', (commission_rate, min_amount, max_amount, product_name))
        else:
            # Insert new rule
            conn.execute('''
                INSERT INTO commission_rule (product_name, commission_rate, min_amount, max_amount)
                VALUES (?, ?, ?, ?)
            ''', (product_name, commission_rate, min_amount, max_amount))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        st.error(f"Error adding commission rule: {e}")
        return False

def get_all_users():
    """Get all users"""
    try:
        conn = get_db_connection()
        if not conn:
            return []
        
        users = conn.execute('''
            SELECT * FROM user ORDER BY username
        ''').fetchall()
        
        conn.close()
        return [dict(user) for user in users]
    except Exception as e:
        st.error(f"Error fetching users: {e}")
        return []

def add_user(username, email, password, role):
    """Add new user"""
    try:
        conn = get_db_connection()
        if not conn:
            return False
        
        conn.execute('''
            INSERT INTO user (username, email, password_hash, role)
            VALUES (?, ?, ?, ?)
        ''', (username, email, password, role))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        st.error(f"Error adding user: {e}")
        return False

def update_user(user_id, username, email, role):
    """Update user information"""
    try:
        conn = get_db_connection()
        if not conn:
            return False
        
        conn.execute('''
            UPDATE user SET username = ?, email = ?, role = ?
            WHERE id = ?
        ''', (username, email, role, user_id))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        st.error(f"Error updating user: {e}")
        return False

def delete_user(user_id):
    """Delete user"""
    try:
        conn = get_db_connection()
        if not conn:
            return False
        
        # Delete user's sales first
        conn.execute('DELETE FROM sale WHERE user_id = ?', (user_id,))
        # Delete user
        conn.execute('DELETE FROM user WHERE id = ?', (user_id,))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        st.error(f"Error deleting user: {e}")
        return False

def add_sale(user_id, customer_name, product_name, amount, commission_rate):
    """Add new sale record"""
    try:
        commission_amount = amount * (commission_rate / 100)
        
        conn = get_db_connection()
        if not conn:
            return False
        
        conn.execute('''
            INSERT INTO sale (user_id, customer_name, product_name, amount, commission_amount, sale_date)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, customer_name, product_name, amount, commission_amount, date.today()))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        st.error(f"Error adding sale: {e}")
        return False

def login_page():
    """Login page"""
    st.title("🔐 Sales Incentive Calculator")
    st.markdown("---")
    
    # Initialize database
    if init_database():
        st.success("✅ Database initialized successfully")
    
    st.subheader("Please Login to Continue")
    
    # Login instructions
    with st.expander("ℹ️ Available Demo Accounts", expanded=True):
        st.info("""
        **👨‍💼 Admin Accounts:**
        - Username: `admin` / Password: `admin123` (System Administrator)
        - Username: `manager` / Password: `manager123` (Sales Manager)
        
        **👤 Sales Rep Accounts:**
        - Username: `salesrep` / Password: `sales123` (Sales Representative)
        - Username: `demo` / Password: `demo123` (Demo Sales Rep)
        
        **Features:**
        - 📊 Sales Dashboard with charts and statistics
        - 💼 Sales Management (add, view, edit sales)
        - ⚙️ Commission Rules Management (admin only)
        - 👥 User Management (admin only)
        """)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("login_form"):
            username = st.text_input("👤 Username", value="admin")
            password = st.text_input("🔒 Password", type="password", value="admin123")
            
            submit = st.form_submit_button("🚀 Login", use_container_width=True)
            
            if submit:
                if username and password:
                    user = authenticate_user(username, password)
                    if user:
                        st.session_state.logged_in = True
                        st.session_state.user = user
                        st.success(f"✅ Welcome {user['username']}! ({user['role']})")
                        st.rerun()
                    else:
                        st.error("❌ Invalid credentials")
                else:
                    st.error("Please enter both username and password")

def dashboard_page():
    """Dashboard page"""
    user = st.session_state.user
    is_admin = user['role'] == 'admin'
    
    st.title(f"📊 Sales Dashboard - Welcome {user['username']}!")
    
    # Get data based on role
    if is_admin:
        stats = get_sales_stats()
        sales_data = get_sales_data()
        st.info("👨‍💼 **Admin View**: Showing all sales data across the organization")
    else:
        stats = get_sales_stats(user['id'])
        sales_data = get_sales_data(user['id'])
        st.info("👤 **Personal View**: Showing your sales data only")
    
    # Display metrics
    if stats and stats.get('total_sales', 0) > 0:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("🎯 Total Sales", stats.get('total_sales', 0))
        with col2:
            st.metric("💰 Total Revenue", f"${stats.get('total_amount', 0):,.2f}")
        with col3:
            st.metric("💵 Total Commission", f"${stats.get('total_commission', 0):,.2f}")
        with col4:
            st.metric("📊 Average Sale", f"${stats.get('average_sale', 0):,.2f}")
        
        st.markdown("---")
        
        # Charts
        if sales_data:
            df = pd.DataFrame(sales_data)
            df['sale_date'] = pd.to_datetime(df['sale_date'])
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Sales over time
                st.subheader("📅 Sales Trend")
                daily_sales = df.groupby('sale_date')['amount'].sum().reset_index()
                
                fig = px.line(daily_sales, x='sale_date', y='amount', 
                             title='Sales Over Time', markers=True)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Product performance
                st.subheader("🏆 Product Performance")
                product_sales = df.groupby('product_name')['amount'].sum().sort_values(ascending=False)
                
                fig = px.pie(values=product_sales.values, names=product_sales.index, 
                            title='Sales by Product')
                st.dataframe(df, width="content")

            
            # Sales table
            st.subheader("📋 Recent Sales Records")
            display_cols = ['customer_name', 'product_name', 'amount', 'commission_amount', 'sale_date']
            if is_admin:
                display_cols.append('salesperson')
            
            recent_sales = df[display_cols].head(10)
            st.dataframe(recent_sales, width="stretch", hide_index=True)

    else:
        st.info("📝 No sales data available")

def sales_management_page():
    """Sales management page"""
    st.title("💼 Sales Management")
    
    user = st.session_state.user
    
    # Add new sale form
    st.subheader("➕ Add New Sale")
    
    with st.form("add_sale_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            customer_name = st.text_input("Customer Name")
            product_name = st.selectbox("Product", 
                ["Premium Package", "Standard Package", "Basic Package", "Enterprise Solution"])
        
        with col2:
            amount = st.number_input("Sale Amount ($)", min_value=0.01, value=1000.00, step=100.00)
            commission_rate = st.number_input("Commission Rate (%)", min_value=0.1, max_value=50.0, value=10.0, step=0.5)
        
        submit = st.form_submit_button("💾 Add Sale", use_container_width=True)
        
        if submit:
            if customer_name and product_name and amount > 0:
                if add_sale(user['id'], customer_name, product_name, amount, commission_rate):
                    st.success(f"✅ Sale added successfully! Commission: ${amount * (commission_rate/100):.2f}")
                    st.rerun()
                else:
                    st.error("❌ Failed to add sale")
            else:
                st.error("Please fill in all required fields")
    
    st.markdown("---")
    
    # Display user's sales
    st.subheader("📊 Your Sales History")
    sales_data = get_sales_data(user['id'])
    
    if sales_data:
        df = pd.DataFrame(sales_data)
        st.dataframe(df[['customer_name', 'product_name', 'amount', 'commission_amount', 'sale_date']], 
                    use_container_width=True, hide_index=True)
    else:
        st.info("No sales records found")

def commission_rules_page():
    """Commission rules management page"""
    st.title("⚙️ Commission Rules Management")
    
    # Add/Edit commission rule form
    st.subheader("➕ Add/Edit Commission Rule")
    
    with st.form("commission_rule_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            product_name = st.text_input("Product Name", value="New Product")
            commission_rate = st.number_input("Commission Rate (%)", min_value=0.1, max_value=50.0, value=10.0, step=0.5)
        
        with col2:
            min_amount = st.number_input("Minimum Sale Amount ($)", min_value=0.0, value=0.0, step=100.00)
            max_amount = st.number_input("Maximum Sale Amount ($) - Leave 0 for no limit", min_value=0.0, value=0.0, step=1000.00)
        
        submit = st.form_submit_button("💾 Save Commission Rule", use_container_width=True)
        
        if submit:
            if product_name and commission_rate > 0:
                max_amt = max_amount if max_amount > 0 else None
                if add_commission_rule(product_name, commission_rate, min_amount, max_amt):
                    st.success(f"✅ Commission rule saved for {product_name}: {commission_rate}%")
                    st.rerun()
                else:
                    st.error("❌ Failed to save commission rule")
            else:
                st.error("Please fill in required fields")
    
    st.markdown("---")
    
    # Display existing commission rules
    st.subheader("📋 Current Commission Rules")
    rules = get_commission_rules()
    
    if rules:
        df = pd.DataFrame(rules)
        df['max_amount'] = df['max_amount'].fillna('No Limit')
        display_df = df[['product_name', 'commission_rate', 'min_amount', 'max_amount']]
        display_df.columns = ['Product', 'Commission Rate (%)', 'Min Amount ($)', 'Max Amount ($)']
        st.dataframe(display_df, use_container_width=True, hide_index=True)
    else:
        st.info("No commission rules found")

def user_management_page():
    """User management page"""
    st.title("👥 User Management")
    
    # Add new user form
    st.subheader("➕ Add New User")
    
    with st.form("add_user_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            new_username = st.text_input("Username")
            new_email = st.text_input("Email")
        
        with col2:
            new_password = st.text_input("Password", type="password")
            new_role = st.selectbox("Role", ["sales_rep", "admin"])
        
        submit = st.form_submit_button("👤 Add User", use_container_width=True)
        
        if submit:
            if new_username and new_email and new_password:
                if add_user(new_username, new_email, new_password, new_role):
                    st.success(f"✅ User {new_username} added successfully!")
                    st.rerun()
                else:
                    st.error("❌ Failed to add user (username/email might already exist)")
            else:
                st.error("Please fill in all fields")
    
    st.markdown("---")
    
    # Display existing users
    st.subheader("📋 Current Users")
    users = get_all_users()
    
    if users:
        for user in users:
            with st.expander(f"👤 {user['username']} ({user['role']})"):
                col1, col2, col3 = st.columns([2, 2, 1])
                
                with col1:
                    st.write(f"**Email:** {user['email']}")
                    st.write(f"**Role:** {user['role']}")
                    st.write(f"**Created:** {user['created_at']}")
                
                with col2:
                    # Get user's sales stats
                    user_stats = get_sales_stats(user['id'])
                    st.metric("Sales Count", user_stats.get('total_sales', 0))
                    st.metric("Total Revenue", f"${user_stats.get('total_amount', 0):,.0f}")
                
                with col3:
                    if st.button(f"🗑️ Delete", key=f"delete_{user['id']}", 
                               help="Delete user and all their sales"):
                        if user['id'] != st.session_state.user['id']:  # Can't delete self
                            if delete_user(user['id']):
                                st.success(f"User {user['username']} deleted")
                                st.rerun()
                        else:
                            st.error("Cannot delete your own account")
    else:
        st.info("No users found")

def main():
    """Main application"""
    if not st.session_state.logged_in:
        login_page()
        return
    
    user = st.session_state.user
    
    # Sidebar navigation
    with st.sidebar:
        st.title("🧭 Navigation")
        st.markdown("---")
        
        st.write(f"👤 **{user['username']}**")
        st.write(f"🎭 Role: {user['role'].replace('_', ' ').title()}")
        st.markdown("---")
        
        # Navigation buttons
        pages = ["📊 Dashboard", "💼 Sales Management"]
        if user['role'] == 'admin':
            pages.extend(["⚙️ Commission Rules", "👥 User Management"])
        
        for page in pages:
            if st.button(page, use_container_width=True):
                st.session_state.current_page = page.split(" ", 1)[1]  # Remove emoji
                st.rerun()
        
        st.markdown("---")
        
        # Quick stats
        if user['role'] == 'admin':
            stats = get_sales_stats()
        else:
            stats = get_sales_stats(user['id'])
        
        if stats:
            st.metric("Your Sales", stats.get('total_sales', 0))
            st.metric("Your Revenue", f"${stats.get('total_amount', 0):,.0f}")
        
        st.markdown("---")
        
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user = None
            st.session_state.current_page = "Dashboard"
            st.rerun()
    
    # Main content based on current page
    if st.session_state.current_page == "Dashboard":
        dashboard_page()
    elif st.session_state.current_page == "Sales Management":
        sales_management_page()
    elif st.session_state.current_page == "Commission Rules":
        commission_rules_page()
    elif st.session_state.current_page == "User Management":
        user_management_page()

if __name__ == "__main__":
    main()