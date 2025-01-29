import streamlit as st
import hashlib
import datetime
import pandas as pd


# ---------------
# Naive Blockchain Classes
# ---------------

class Block:
    def __init__(self, index, timestamp, data, previous_hash):
        self.index = index
        self.timestamp = timestamp
        self.data = data  # dict: {title, description, doc_hash, patent_type, is_on_blockchain}
        self.previous_hash = previous_hash
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        block_string = (
                str(self.index)
                + str(self.timestamp)
                + str(self.data)
                + str(self.previous_hash)
        )
        return hashlib.sha256(block_string.encode()).hexdigest()


class Blockchain:
    def __init__(self):
        self.chain = [self.create_genesis_block()]

    def create_genesis_block(self):
        return Block(
            index=0,
            timestamp=str(datetime.datetime.now()),
            data={
                "title": "Genesis Block",
                "description": "",
                "doc_hash": "",
                "patent_type": "",
                "is_on_blockchain": True,
            },
            previous_hash="0"
        )

    def get_latest_block(self):
        return self.chain[-1]

    def add_block(self, new_block):
        new_block.previous_hash = self.get_latest_block().hash
        new_block.hash = new_block.calculate_hash()
        self.chain.append(new_block)


# ---------------
# Helper Functions
# ---------------

def hash_file_bytes(file_bytes):
    """Return a SHA-256 hex digest for file bytes."""
    return hashlib.sha256(file_bytes).hexdigest()


def initialize_session_state():
    """
    Create or retrieve our data structures in st.session_state,
    so we don't lose them on each re-run.
    """
    if "toy_chain" not in st.session_state:
        st.session_state.toy_chain = Blockchain()
    if "off_chain_list" not in st.session_state:
        st.session_state.off_chain_list = []  # store off-chain patents in a list

    # Define a fixed set of patent types
    patent_types_list = [
        "Utility Patent",
        "Design Patent",
        "Plant Patent",
        "Certificate of Amendment",
        "Other"
    ]
    if "patent_types" not in st.session_state:
        st.session_state.patent_types = patent_types_list

    # Keep separate counters for on-chain vs off-chain
    if "counts_on_chain" not in st.session_state:
        st.session_state.counts_on_chain = {ptype: 0 for ptype in patent_types_list}
    if "counts_off_chain" not in st.session_state:
        st.session_state.counts_off_chain = {ptype: 0 for ptype in patent_types_list}


# ---------------
# Streamlit App
# ---------------
def main():
    # Initialize session state data
    initialize_session_state()

    st.set_page_config(page_title="Fashionable Patent Demo", layout="centered")

    # Custom CSS for a modern look
    st.markdown(
        """
        <style>
        /* Make the main panel a bit wider */
        .main > div {
            max-width: 800px;
        }
        /* Stylish heading */
        h1, h2, h3 {
            color: #2c3e50;
            font-family: "Trebuchet MS", sans-serif;
        }
        /* Card-like block styling */
        .block-container {
            background-color: #f9f9f9;
            padding: 16px;
            border-radius: 8px;
        }
        .title-text {
            color: #2980b9;
        }
        .hash-text {
            font-size: 10pt;
            color: #7f8c8d;
            word-wrap: break-word;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Header
    st.title("Patent Registration with Timestamp")
    st.write(
        "An UI to demonstrate storing patent data **on** or **off** a simple blockchain, "
        "with a timestamp and a chart of patent types. Data persists in session state."
    )
    st.write("---")

    # --- 1) SUBMIT A NEW PATENT ---
    st.header("1) Submit a New Patent")
    st.write("Fill in the form below to submit your patent data.")

    with st.form("patent_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            patent_title = st.text_input("Invention Title *", max_chars=80)
            patent_type = st.selectbox("Patent Type", options=st.session_state.patent_types)
        with col2:
            store_option = st.radio("Store patent:", ("On Blockchain", "Off Blockchain"))

        patent_description = st.text_area("Brief Description", height=80)
        uploaded_file = st.file_uploader("Attach File (optional)", type=["pdf", "txt", "png", "jpg"])

        submitted = st.form_submit_button("Submit Patent")

        if submitted:
            if not patent_title:
                st.warning("Please provide a title.")
            else:
                # Compute doc hash if file uploaded or else from description
                doc_hash = ""
                if uploaded_file is not None:
                    doc_hash = hash_file_bytes(uploaded_file.read())
                elif patent_description.strip():
                    doc_hash = hashlib.sha256(patent_description.encode()).hexdigest()

                # Gather all data
                block_data = {
                    "title": patent_title,
                    "description": patent_description,
                    "doc_hash": doc_hash,
                    "patent_type": patent_type,
                    "is_on_blockchain": (store_option == "On Blockchain"),
                }

                if block_data["is_on_blockchain"]:
                    # Add to the naive blockchain
                    new_block = Block(
                        index=len(st.session_state.toy_chain.chain),
                        timestamp=str(datetime.datetime.now()),
                        data=block_data,
                        previous_hash=""
                    )
                    st.session_state.toy_chain.add_block(new_block)
                    # Update on-chain count
                    st.session_state.counts_on_chain[patent_type] += 1
                    st.success("Patent data recorded **on** the toy blockchain!")
                else:
                    # Just store off-chain
                    st.session_state.off_chain_list.append({
                        "timestamp": str(datetime.datetime.now()),
                        "data": block_data
                    })
                    st.session_state.counts_off_chain[patent_type] += 1
                    st.success("Patent data recorded **off** the blockchain (in local list).")

                st.balloons()

    # --- 2) VIEW CURRENT RECORDS ---
    st.write("---")
    st.header("2) View Patent Records")

    tab1, tab2 = st.tabs(["On Blockchain", "Off Blockchain"])

    with tab1:
        st.subheader("Blockchain Blocks")
        chain = st.session_state.toy_chain.chain
        for block in chain:
            st.markdown("### ---")
            st.markdown(f"**Block #{block.index}**")
            st.write(f"**Timestamp:** {block.timestamp}")
            st.write(f"**Title:** {block.data.get('title', '')}")
            st.write(f"**Description:** {block.data.get('description', '')}")
            st.write(f"**Patent Type:** {block.data.get('patent_type', '')}")
            doc_hash = block.data.get("doc_hash", "")
            if doc_hash:
                st.markdown(f"**Document Hash**:  \n```\n{doc_hash}\n```")
            st.markdown(f"**Previous Hash**:  \n<small class='hash-text'>{block.previous_hash}</small>",
                        unsafe_allow_html=True)
            st.markdown(f"**Block Hash**:  \n<small class='hash-text'>{block.hash}</small>", unsafe_allow_html=True)

    with tab2:
        st.subheader("Off-Chain Submissions")
        if len(st.session_state.off_chain_list) == 0:
            st.write("No off-chain records yet.")
        else:
            for i, record in enumerate(st.session_state.off_chain_list):
                st.markdown("### ---")
                st.markdown(f"**Record #{i}**")
                st.write(f"**Timestamp:** {record['timestamp']}")
                data = record["data"]
                st.write(f"**Title:** {data.get('title', '')}")
                st.write(f"**Description:** {data.get('description', '')}")
                st.write(f"**Patent Type:** {data.get('patent_type', '')}")
                doc_hash = data.get("doc_hash", "")
                if doc_hash:
                    st.markdown(f"**Document Hash**:  \n```\n{doc_hash}\n```")

    # --- 3) DISPLAY PATENT STATISTICS ---
    st.write("---")
    st.header("3) Patent Statistics")
    st.write("Count of patents by type, on-chain vs off-chain:")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("On-Chain Distribution")
        df_on_chain = pd.DataFrame({
            "Patent Type": list(st.session_state.counts_on_chain.keys()),
            "Count": list(st.session_state.counts_on_chain.values())
        })
        st.bar_chart(data=df_on_chain, x="Patent Type", y="Count", height=300)

    with col2:
        st.subheader("Off-Chain Distribution")
        df_off_chain = pd.DataFrame({
            "Patent Type": list(st.session_state.counts_off_chain.keys()),
            "Count": list(st.session_state.counts_off_chain.values())
        })
        st.bar_chart(data=df_off_chain, x="Patent Type", y="Count", height=300)



if __name__ == "__main__":
    main()
