import streamlit as st
import yaml
import os
from components import id_to_a4, id_front_back, id_center, multi_id_center

# Load config
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Sidebar: Help, Settings, Reset
st.sidebar.title("🛠️ Settings & Help")
st.sidebar.markdown("**DPI (Print Quality):**")
dpi = st.sidebar.slider("DPI", 72, 600, 300, 10, key="dpi_global")
st.sidebar.markdown("---")
st.sidebar.markdown("**About:**\nThis app helps you print ID cards, documents, and photos in custom layouts, with cropping, enhancement, and batch support.\n\n**Tips:**\n- Use the crop sliders to trim your image.\n- Adjust brightness/contrast for best print results.\n- Choose the right page and document size for your needs.\n- Download as PDF or Word for easy printing.")
if st.sidebar.button("🔁 Reset All"):
    st.session_state.clear()
    st.rerun()

# Pass global settings to config/session
config['dpi'] = dpi

st.title("🪪 Card Printing Suite")

# Tabs for each feature
TABS = [
    "ID to A4 (8 per page)",
    "ID to A4 (Front & Back)",
    "Single ID Centered",
    "Multiple IDs Centered"
]
tab1, tab2, tab3, tab4 = st.tabs(TABS)

with tab1:
    st.markdown("Easily print 8 documents per page. [Tip: Use crop and enhancement for best results!]")
    id_to_a4.render(st, config)
with tab2:
    st.markdown("Print front and back of a document on a single page.")
    id_front_back.render(st, config)
with tab3:
    st.markdown("Print a single document centered on the page.")
    id_center.render(st, config)
with tab4:
    st.markdown("Print up to 4 documents, spaced and centered.")
    multi_id_center.render(st, config) 