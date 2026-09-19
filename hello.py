import streamlit as st

normal = 0
if "count" not in st.session_state:
    st.session_state.count = 0

if st.button("Click me"):
    normal += 1
    st.session_state.count += 1

st.write("Normal variable:", normal)
st.write("Session state:", st.session_state.count)
