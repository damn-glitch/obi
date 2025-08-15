import streamlit as st
import hashlib
import datetime
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
import uuid
from typing import Dict, List, Optional
import base64
from io import BytesIO

# ---------------
# Enhanced Blockchain Classes
# ---------------

class Block:
    def __init__(self, index, timestamp, data, previous_hash, nonce=0):
        self.index = index
        self.timestamp = timestamp
        self.data = data
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.hash = self.calculate_hash()
        self.merkle_root = self.calculate_merkle_root()

    def calculate_hash(self):
        block_string = (
            str(self.index) +
            str(self.timestamp) +
            json.dumps(self.data, sort_keys=True) +
            str(self.previous_hash) +
            str(self.nonce)
        )
        return hashlib.sha256(block_string.encode()).hexdigest()

    def calculate_merkle_root(self):
        """Simplified Merkle root calculation"""
        data_string = json.dumps(self.data, sort_keys=True)
        return hashlib.sha256(data_string.encode()).hexdigest()

    def mine_block(self, difficulty=2):
        """Simple proof of work mining"""
        target = "0" * difficulty
        while self.hash[:difficulty] != target:
            self.nonce += 1
            self.hash = self.calculate_hash()

class Blockchain:
    def __init__(self):
        self.chain = [self.create_genesis_block()]
        self.difficulty = 2
        self.pending_transactions = []
        self.mining_reward = 100

    def create_genesis_block(self):
        genesis_block = Block(
            index=0,
            timestamp=str(datetime.datetime.now()),
            data={
                "title": "Genesis Block",
                "description": "First block in the patent blockchain",
                "doc_hash": "",
                "patent_type": "Genesis",
                "is_on_blockchain": True,
                "patent_id": "GENESIS-000",
                "inventor": "System",
                "status": "Active",
                "priority": "Normal"
            },
            previous_hash="0"
        )
        genesis_block.mine_block(self.difficulty)
        return genesis_block

    def get_latest_block(self):
        return self.chain[-1]

    def add_block(self, new_block):
        new_block.previous_hash = self.get_latest_block().hash
        new_block.mine_block(self.difficulty)
        self.chain.append(new_block)

    def is_chain_valid(self):
        """Validate the entire blockchain"""
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i-1]
            
            if current_block.hash != current_block.calculate_hash():
                return False
            if current_block.previous_hash != previous_block.hash:
                return False
        return True

# ---------------
# Data Models
# ---------------

class Patent:
    def __init__(self, title, description, inventor, patent_type, priority="Normal"):
        self.id = f"PAT-{str(uuid.uuid4())[:8].upper()}"
        self.title = title
        self.description = description
        self.inventor = inventor
        self.patent_type = patent_type
        self.priority = priority
        self.created_at = datetime.datetime.now()
        self.status = "Pending"
        self.file_hash = None
        self.verification_score = 0

class User:
    def __init__(self, username, role="Inventor"):
        self.username = username
        self.role = role  # Inventor, Examiner, Admin
        self.created_at = datetime.datetime.now()
        self.patents_submitted = 0
        self.last_login = datetime.datetime.now()

# ---------------
# Utility Functions
# ---------------

def hash_file_bytes(file_bytes):
    """Return a SHA-256 hex digest for file bytes."""
    return hashlib.sha256(file_bytes).hexdigest()

def generate_patent_id():
    """Generate a unique patent ID"""
    return f"PAT-{str(uuid.uuid4())[:8].upper()}"

def verify_patent_authenticity(patent_data):
    """Simulate patent verification process"""
    score = 50  # Base score
    
    # Check title length and complexity
    if len(patent_data.get("title", "")) > 10:
        score += 10
    
    # Check description length
    if len(patent_data.get("description", "")) > 50:
        score += 15
    
    # Check if file is attached
    if patent_data.get("doc_hash"):
        score += 20
    
    # Random factor for demonstration
    import random
    score += random.randint(-5, 15)
    
    return min(100, max(0, score))

def get_file_size_str(size_bytes):
    """Convert bytes to human readable format"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024**2:
        return f"{size_bytes/1024:.1f} KB"
    elif size_bytes < 1024**3:
        return f"{size_bytes/(1024**2):.1f} MB"
    else:
        return f"{size_bytes/(1024**3):.1f} GB"

def initialize_session_state():
    """Initialize all session state variables"""
    
    # Core blockchain and data
    if "toy_chain" not in st.session_state:
        st.session_state.toy_chain = Blockchain()
    if "off_chain_list" not in st.session_state:
        st.session_state.off_chain_list = []
    
    # Enhanced patent types
    patent_types_list = [
        "Utility Patent", "Design Patent", "Plant Patent", 
        "Provisional Patent", "Software Patent", "Business Method Patent",
        "Biotechnology Patent", "Chemical Patent", "Mechanical Patent",
        "Certificate of Amendment", "Other"
    ]
    if "patent_types" not in st.session_state:
        st.session_state.patent_types = patent_types_list

    # User management
    if "current_user" not in st.session_state:
        st.session_state.current_user = User("demo_user", "Inventor")
    if "users" not in st.session_state:
        st.session_state.users = {
            "demo_user": User("demo_user", "Inventor"),
            "examiner1": User("examiner1", "Examiner"),
            "admin": User("admin", "Admin")
        }

    # Statistics
    if "counts_on_chain" not in st.session_state:
        st.session_state.counts_on_chain = {ptype: 0 for ptype in patent_types_list}
    if "counts_off_chain" not in st.session_state:
        st.session_state.counts_off_chain = {ptype: 0 for ptype in patent_types_list}
    
    # Notifications
    if "notifications" not in st.session_state:
        st.session_state.notifications = []
    
    # Search and filter states
    if "search_term" not in st.session_state:
        st.session_state.search_term = ""
    if "filter_type" not in st.session_state:
        st.session_state.filter_type = "All"

def add_notification(message, type="info"):
    """Add a notification to the system"""
    notification = {
        "id": str(uuid.uuid4())[:8],
        "message": message,
        "type": type,  # info, success, warning, error
        "timestamp": datetime.datetime.now(),
        "read": False
    }
    st.session_state.notifications.insert(0, notification)

def get_blockchain_stats():
    """Get comprehensive blockchain statistics"""
    chain = st.session_state.toy_chain.chain
    stats = {
        "total_blocks": len(chain),
        "total_patents": len(chain) - 1,  # Exclude genesis block
        "chain_valid": st.session_state.toy_chain.is_chain_valid(),
        "average_block_time": 0,
        "total_hash_power": sum(block.nonce for block in chain),
        "latest_block_hash": chain[-1].hash if chain else "N/A"
    }
    
    if len(chain) > 1:
        timestamps = [datetime.datetime.fromisoformat(block.timestamp) for block in chain[1:]]
        if len(timestamps) > 1:
            time_diffs = [(timestamps[i] - timestamps[i-1]).total_seconds() for i in range(1, len(timestamps))]
            stats["average_block_time"] = sum(time_diffs) / len(time_diffs)
    
    return stats

# ---------------
# UI Components
# ---------------

def render_sidebar():
    """Render the enhanced sidebar"""
    with st.sidebar:
        st.image("https://via.placeholder.com/200x80/2E86AB/FFFFFF?text=PatentChain", width=200)
        
        # User info
        st.markdown("---")
        st.markdown(f"**👤 User:** {st.session_state.current_user.username}")
        st.markdown(f"**🎭 Role:** {st.session_state.current_user.role}")
        st.markdown(f"**📅 Member since:** {st.session_state.current_user.created_at.strftime('%Y-%m-%d')}")
        
        # Quick stats
        st.markdown("---")
        st.markdown("**📊 Quick Stats**")
        stats = get_blockchain_stats()
        st.metric("Total Patents", stats["total_patents"])
        st.metric("Blockchain Health", "✅ Valid" if stats["chain_valid"] else "❌ Invalid")
        
        # Notifications
        st.markdown("---")
        unread_count = sum(1 for n in st.session_state.notifications if not n["read"])
        if st.button(f"🔔 Notifications ({unread_count})"):
            st.session_state.show_notifications = True
        
        # Navigation
        st.markdown("---")
        st.markdown("**🧭 Quick Navigation**")
        if st.button("📝 Submit Patent", use_container_width=True):
            st.rerun()
        if st.button("🔍 Search Patents", use_container_width=True):
            st.session_state.active_tab = "search"
        if st.button("📈 Analytics", use_container_width=True):
            st.session_state.active_tab = "analytics"

def render_notification_panel():
    """Render notifications in an expandable panel"""
    if st.session_state.notifications:
        with st.expander(f"🔔 Notifications ({len(st.session_state.notifications)})", expanded=False):
            for notification in st.session_state.notifications[:5]:  # Show latest 5
                icon = {"info": "ℹ️", "success": "✅", "warning": "⚠️", "error": "❌"}.get(notification["type"], "ℹ️")
                st.markdown(f"{icon} **{notification['timestamp'].strftime('%H:%M')}** - {notification['message']}")

def render_advanced_search():
    """Render advanced search and filter interface"""
    st.subheader("🔍 Advanced Patent Search")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        search_term = st.text_input("Search patents...", 
                                   placeholder="Enter keywords, patent ID, or inventor name",
                                   value=st.session_state.search_term)
    
    with col2:
        filter_type = st.selectbox("Filter by Type", 
                                  ["All"] + st.session_state.patent_types,
                                  index=0 if st.session_state.filter_type == "All" else 
                                  st.session_state.patent_types.index(st.session_state.filter_type) + 1)
    
    with col3:
        filter_status = st.selectbox("Filter by Status", ["All", "Active", "Pending", "Approved", "Rejected"])
    
    # Advanced filters
    with st.expander("🔧 Advanced Filters"):
        col1, col2 = st.columns(2)
        with col1:
            date_from = st.date_input("From Date", value=datetime.date.today() - datetime.timedelta(days=30))
            priority_filter = st.multiselect("Priority", ["Low", "Normal", "High", "Critical"])
        with col2:
            date_to = st.date_input("To Date", value=datetime.date.today())
            storage_filter = st.selectbox("Storage", ["All", "On-Chain", "Off-Chain"])
    
    return {
        "search_term": search_term,
        "filter_type": filter_type,
        "filter_status": filter_status,
        "date_from": date_from,
        "date_to": date_to,
        "priority_filter": priority_filter,
        "storage_filter": storage_filter
    }

def render_analytics_dashboard():
    """Render comprehensive analytics dashboard"""
    st.header("📈 Patent Analytics Dashboard")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    stats = get_blockchain_stats()
    total_on_chain = sum(st.session_state.counts_on_chain.values())
    total_off_chain = sum(st.session_state.counts_off_chain.values())
    
    with col1:
        st.metric("Total Patents", total_on_chain + total_off_chain)
    with col2:
        st.metric("On-Chain Patents", total_on_chain)
    with col3:
        st.metric("Off-Chain Patents", total_off_chain)
    with col4:
        st.metric("Blockchain Blocks", stats["total_blocks"])
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Patent type distribution
        fig_pie = px.pie(
            values=list(st.session_state.counts_on_chain.values()) + list(st.session_state.counts_off_chain.values()),
            names=list(st.session_state.counts_on_chain.keys()) + [f"{k} (Off-Chain)" for k in st.session_state.counts_off_chain.keys()],
            title="Patent Distribution by Type and Storage"
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        # Timeline chart (simulated)
        dates = pd.date_range(start=datetime.date.today() - datetime.timedelta(days=30), 
                             end=datetime.date.today(), freq='D')
        values = [abs(hash(str(date)) % 10) for date in dates]
        
        fig_line = px.line(x=dates, y=values, title="Patent Submissions Over Time")
        fig_line.update_layout(xaxis_title="Date", yaxis_title="Number of Patents")
        st.plotly_chart(fig_line, use_container_width=True)
    
    # Blockchain health metrics
    st.subheader("⛓️ Blockchain Health Metrics")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Chain Validity", "✅ Valid" if stats["chain_valid"] else "❌ Invalid")
    with col2:
        st.metric("Average Block Time", f"{stats['average_block_time']:.2f}s")
    with col3:
        st.metric("Total Mining Power", f"{stats['total_hash_power']:,}")

def render_blockchain_explorer():
    """Render detailed blockchain explorer"""
    st.subheader("⛓️ Blockchain Explorer")
    
    chain = st.session_state.toy_chain.chain
    
    # Chain overview
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Blocks", len(chain))
    with col2:
        st.metric("Latest Block", f"#{len(chain)-1}")
    with col3:
        latest_hash = chain[-1].hash[:16] + "..." if chain else "N/A"
        st.metric("Latest Hash", latest_hash)
    
    # Block explorer
    if chain:
        block_index = st.selectbox("Select Block to Explore", 
                                  range(len(chain)), 
                                  format_func=lambda x: f"Block #{x}" + (" (Genesis)" if x == 0 else ""))
        
        block = chain[block_index]
        
        with st.container():
            st.markdown(f"""
            <div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; margin: 10px 0;">
                <h4>Block #{block.index}</h4>
                <p><strong>Timestamp:</strong> {block.timestamp}</p>
                <p><strong>Hash:</strong> <code>{block.hash}</code></p>
                <p><strong>Previous Hash:</strong> <code>{block.previous_hash}</code></p>
                <p><strong>Merkle Root:</strong> <code>{block.merkle_root}</code></p>
                <p><strong>Nonce:</strong> {block.nonce}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Block data
            st.json(block.data)

def export_data():
    """Export patent data to various formats"""
    st.subheader("📤 Export Patent Data")
    
    export_format = st.selectbox("Select Export Format", ["CSV", "JSON", "Excel"])
    include_blockchain = st.checkbox("Include Blockchain Data", value=True)
    include_offchain = st.checkbox("Include Off-Chain Data", value=True)
    
    if st.button("Generate Export"):
        data = []
        
        if include_blockchain:
            for block in st.session_state.toy_chain.chain[1:]:  # Skip genesis
                data.append({
                    "source": "blockchain",
                    "block_index": block.index,
                    "timestamp": block.timestamp,
                    "hash": block.hash,
                    **block.data
                })
        
        if include_offchain:
            for i, record in enumerate(st.session_state.off_chain_list):
                data.append({
                    "source": "off-chain",
                    "record_index": i,
                    "timestamp": record["timestamp"],
                    "hash": "N/A",
                    **record["data"]
                })
        
        if data:
            df = pd.DataFrame(data)
            
            if export_format == "CSV":
                csv = df.to_csv(index=False)
                st.download_button("Download CSV", csv, "patents.csv", "text/csv")
            elif export_format == "JSON":
                json_str = df.to_json(orient="records", indent=2)
                st.download_button("Download JSON", json_str, "patents.json", "application/json")
            elif export_format == "Excel":
                buffer = BytesIO()
                df.to_excel(buffer, index=False)
                st.download_button("Download Excel", buffer.getvalue(), "patents.xlsx", 
                                 "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# ---------------
# Main Application
# ---------------

def main():
    # Initialize session state
    initialize_session_state()
    
    # Page configuration
    st.set_page_config(
        page_title="PatentChain - Advanced Patent Management System",
        page_icon="⛓️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Enhanced CSS styling
    st.markdown("""
    <style>
    .main > div {
        padding-top: 2rem;
    }
    
    .stApp > header {
        background-color: transparent;
    }
    
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        min-height: 100vh;
    }
    
    .main .block-container {
        background-color: white;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 2rem;
    }
    
    h1, h2, h3 {
        color: #2c3e50;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    .metric-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
    }
    
    .patent-card {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .status-active { color: #28a745; font-weight: bold; }
    .status-pending { color: #ffc107; font-weight: bold; }
    .status-approved { color: #17a2b8; font-weight: bold; }
    .status-rejected { color: #dc3545; font-weight: bold; }
    
    .priority-high { background-color: #dc3545; color: white; padding: 2px 8px; border-radius: 4px; }
    .priority-normal { background-color: #28a745; color: white; padding: 2px 8px; border-radius: 4px; }
    .priority-low { background-color: #6c757d; color: white; padding: 2px 8px; border-radius: 4px; }
    </style>
    """, unsafe_allow_html=True)
    
    # Render sidebar
    render_sidebar()
    
    # Header
    st.title("⛓️ PatentChain - Advanced Patent Management System")
    st.markdown("*Secure, transparent, and efficient patent registration on blockchain*")
    
    # Notification panel
    render_notification_panel()
    
    # Main navigation tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📝 Submit Patent", 
        "🔍 Search & Browse", 
        "⛓️ Blockchain Explorer", 
        "📈 Analytics", 
        "📤 Export Data",
        "⚙️ System Info"
    ])
    
    with tab1:
        # Enhanced patent submission form
        st.header("📝 Submit New Patent")
        
        with st.form("enhanced_patent_form", clear_on_submit=True):
            # Basic information
            col1, col2 = st.columns(2)
            
            with col1:
                patent_title = st.text_input("Patent Title *", max_chars=100,
                                           help="Enter a descriptive title for your invention")
                inventor_name = st.text_input("Inventor Name *", 
                                            value=st.session_state.current_user.username,
                                            help="Primary inventor or applicant name")
                patent_type = st.selectbox("Patent Type *", 
                                         options=st.session_state.patent_types,
                                         help="Select the most appropriate patent category")
            
            with col2:
                priority = st.selectbox("Priority Level", ["Low", "Normal", "High", "Critical"])
                store_option = st.radio("Storage Option", 
                                       ("On Blockchain", "Off Blockchain"),
                                       help="Blockchain storage provides immutability but costs more")
                estimated_value = st.number_input("Estimated Value ($)", min_value=0, value=10000,
                                                help="Estimated commercial value of the patent")
            
            # Description
            patent_description = st.text_area("Detailed Description *", 
                                             height=150,
                                             help="Provide a comprehensive description of your invention")
            
            # File upload with preview
            col1, col2 = st.columns([2, 1])
            with col1:
                uploaded_file = st.file_uploader(
                    "Attach Supporting Documents", 
                    type=["pdf", "txt", "png", "jpg", "docx", "xlsx"],
                    help="Upload relevant documents, diagrams, or specifications"
                )
            
            with col2:
                if uploaded_file:
                    file_size = get_file_size_str(len(uploaded_file.read()))
                    uploaded_file.seek(0)  # Reset file pointer
                    st.success(f"File: {uploaded_file.name}")
                    st.info(f"Size: {file_size}")
            
            # Additional metadata
            with st.expander("📋 Additional Information"):
                col1, col2 = st.columns(2)
                with col1:
                    keywords = st.text_input("Keywords (comma-separated)", 
                                           help="Enter relevant keywords for searchability")
                    related_patents = st.text_input("Related Patent IDs", 
                                                   help="Reference any related or prior patents")
                with col2:
                    collaboration = st.text_input("Co-inventors", 
                                                 help="List any co-inventors or collaborators")
                    funding_source = st.text_input("Funding Source", 
                                                  help="Grant number, company, or funding organization")
            
            # Terms and conditions
            agree_terms = st.checkbox("I agree to the terms and conditions and confirm the originality of this work *")
            
            # Submit button
            submitted = st.form_submit_button("🚀 Submit Patent Application", 
                                            disabled=not agree_terms,
                                            use_container_width=True)
            
            if submitted:
                if not all([patent_title, inventor_name, patent_description]):
                    st.error("Please fill in all required fields marked with *")
                else:
                    # Process file
                    doc_hash = ""
                    if uploaded_file is not None:
                        file_bytes = uploaded_file.read()
                        doc_hash = hash_file_bytes(file_bytes)
                        uploaded_file.seek(0)
                    elif patent_description.strip():
                        doc_hash = hashlib.sha256(patent_description.encode()).hexdigest()
                    
                    # Generate patent ID
                    patent_id = generate_patent_id()
                    
                    # Create enhanced patent data
                    patent_data = {
                        "patent_id": patent_id,
                        "title": patent_title,
                        "description": patent_description,
                        "inventor": inventor_name,
                        "patent_type": patent_type,
                        "priority": priority,
                        "doc_hash": doc_hash,
                        "estimated_value": estimated_value,
                        "keywords": keywords,
                        "related_patents": related_patents,
                        "collaboration": collaboration,
                        "funding_source": funding_source,
                        "is_on_blockchain": (store_option == "On Blockchain"),
                        "status": "Pending",
                        "verification_score": verify_patent_authenticity({
                            "title": patent_title, 
                            "description": patent_description, 
                            "doc_hash": doc_hash
                        }),
                        "created_by": st.session_state.current_user.username,
                        "file_name": uploaded_file.name if uploaded_file else None,
                        "file_size": len(uploaded_file.read()) if uploaded_file else 0
                    }
                    
                    if uploaded_file:
                        uploaded_file.seek(0)  # Reset for next use
                    
                    # Store the patent
                    if patent_data["is_on_blockchain"]:
                        new_block = Block(
                            index=len(st.session_state.toy_chain.chain),
                            timestamp=str(datetime.datetime.now()),
                            data=patent_data,
                            previous_hash=""
                        )
                        
                        # Show mining progress
                        with st.spinner("Mining block... This may take a moment."):
                            time.sleep(2)  # Simulate mining time
                            st.session_state.toy_chain.add_block(new_block)
                        
                        st.session_state.counts_on_chain[patent_type] += 1
                        add_notification(f"Patent {patent_id} successfully recorded on blockchain!", "success")
                        st.success(f"🎉 Patent {patent_id} successfully recorded on the blockchain!")
                        
                    else:
                        st.session_state.off_chain_list.append({
                            "timestamp": str(datetime.datetime.now()),
                            "data": patent_data
                        })
                        st.session_state.counts_off_chain[patent_type] += 1
                        add_notification(f"Patent {patent_id} stored off-chain", "info")
                        st.success(f"📄 Patent {patent_id} stored off-chain successfully!")
                    
                    # Update user stats
                    st.session_state.current_user.patents_submitted += 1
                    
                    # Show verification score
                    score = patent_data["verification_score"]
                    if score >= 80:
                        st.success(f"🏆 High verification score: {score}/100")
                    elif score >= 60:
                        st.info(f"✅ Good verification score: {score}/100")
                    else:
                        st.warning(f"⚠️ Low verification score: {score}/100 - Consider adding more details")
                    
                    st.balloons()
    
    with tab2:
        # Enhanced search and browse interface
        filters = render_advanced_search()
        
        # Get all patents
        all_patents = []
        
        # From blockchain
        for block in st.session_state.toy_chain.chain[1:]:  # Skip genesis
            patent = block.data.copy()
            patent["source"] = "blockchain"
            patent["block_index"] = block.index
            patent["hash"] = block.hash
            all_patents.append(patent)
        
        # From off-chain
        for i, record in enumerate(st.session_state.off_chain_list):
            patent = record["data"].copy()
            patent["source"] = "off-chain"
            patent["record_index"] = i
            patent["timestamp"] = record["timestamp"]
            all_patents.append(patent)
        
        # Apply filters
        filtered_patents = all_patents
        
        if filters["search_term"]:
            filtered_patents = [p for p in filtered_patents 
                               if filters["search_term"].lower() in p.get("title", "").lower() 
                               or filters["search_term"].lower() in p.get("description", "").lower()
                               or filters["search_term"].lower() in p.get("inventor", "").lower()]
        
        if filters["filter_type"] != "All":
            filtered_patents = [p for p in filtered_patents 
                               if p.get("patent_type") == filters["filter_type"]]
        
        # Display results
        st.subheader(f"📋 Patent Results ({len(filtered_patents)} found)")
        
        if filtered_patents:
            # Sort options
            sort_by = st.selectbox("Sort by", ["Newest First", "Oldest First", "Title A-Z", "Verification Score"])
            
            if sort_by == "Newest First":
                filtered_patents.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            elif sort_by == "Oldest First":
                filtered_patents.sort(key=lambda x: x.get("timestamp", ""))
            elif sort_by == "Title A-Z":
                filtered_patents.sort(key=lambda x: x.get("title", ""))
            elif sort_by == "Verification Score":
                filtered_patents.sort(key=lambda x: x.get("verification_score", 0), reverse=True)
            
            # Display patents
            for patent in filtered_patents:
                with st.container():
                    st.markdown(f"""
                    <div class="patent-card">
                        <div style="display: flex; justify-content: space-between; align-items: start;">
                            <div>
                                <h4>{patent.get('title', 'Untitled')}</h4>
                                <p><strong>ID:</strong> {patent.get('patent_id', 'N/A')} | 
                                   <strong>Type:</strong> {patent.get('patent_type', 'Unknown')} | 
                                   <strong>Inventor:</strong> {patent.get('inventor', 'Unknown')}</p>
                                <p><strong>Description:</strong> {patent.get('description', 'No description')[:200]}{'...' if len(patent.get('description', '')) > 200 else ''}</p>
                                <p><strong>Storage:</strong> {'🔗 Blockchain' if patent.get('is_on_blockchain') else '📁 Off-Chain'} | 
                                   <strong>Created:</strong> {patent.get('timestamp', 'Unknown')[:19]}</p>
                            </div>
                            <div style="text-align: right;">
                                <span class="priority-{patent.get('priority', 'normal').lower()}">{patent.get('priority', 'Normal')}</span><br>
                                <span class="status-{patent.get('status', 'pending').lower()}">{patent.get('status', 'Pending')}</span><br>
                                <small>Score: {patent.get('verification_score', 0)}/100</small>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("No patents found matching your search criteria.")
    
    with tab3:
        render_blockchain_explorer()
    
    with tab4:
        render_analytics_dashboard()
    
    with tab5:
        export_data()
    
    with tab6:
        # System information
        st.header("⚙️ System Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 System Statistics")
            stats = get_blockchain_stats()
            
            st.json({
                "Blockchain Status": "Active",
                "Total Blocks": stats["total_blocks"],
                "Chain Validity": stats["chain_valid"],
                "Mining Difficulty": st.session_state.toy_chain.difficulty,
                "Total Hash Power": stats["total_hash_power"],
                "Average Block Time": f"{stats['average_block_time']:.2f}s",
                "Total Users": len(st.session_state.users),
                "Current User": st.session_state.current_user.username,
                "Total Notifications": len(st.session_state.notifications)
            })
        
        with col2:
            st.subheader("🔧 System Tools")
            
            if st.button("🔄 Validate Blockchain"):
                with st.spinner("Validating blockchain integrity..."):
                    time.sleep(1)
                    is_valid = st.session_state.toy_chain.is_chain_valid()
                    if is_valid:
                        st.success("✅ Blockchain is valid!")
                    else:
                        st.error("❌ Blockchain validation failed!")
            
            if st.button("🧹 Clear Notifications"):
                st.session_state.notifications = []
                st.success("Notifications cleared!")
            
            if st.button("📊 Generate System Report"):
                report = {
                    "timestamp": str(datetime.datetime.now()),
                    "system_stats": get_blockchain_stats(),
                    "user_count": len(st.session_state.users),
                    "patent_counts": {
                        "on_chain": sum(st.session_state.counts_on_chain.values()),
                        "off_chain": sum(st.session_state.counts_off_chain.values())
                    }
                }
                st.json(report)
                st.download_button("Download Report", 
                                 json.dumps(report, indent=2), 
                                 "system_report.json", 
                                 "application/json")

if __name__ == "__main__":
    main()
