# Short-term rental market dashboard on Azure Cosmos DB for MongoDB
# run: streamlit run app.py   (reads MONGO_URI and MONGO_DB from .env or Streamlit secrets)
import streamlit as st

st.set_page_config(page_title="Rental Market Board", layout="wide", initial_sidebar_state="collapsed")
# landscape board first, detailed scrolling board with the 3D map second
nav = st.navigation([st.Page("landscape.py", title="Board", icon=":material/dashboard:", default=True),
                     st.Page("detailed.py", title="Detailed", icon=":material/view_agenda:")], position="top")
nav.run()
