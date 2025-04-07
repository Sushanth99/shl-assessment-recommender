import streamlit as st
import pandas as pd
import requests
import json
import time

SEARCH_ENDPOINT = "https://shl-assessment-recommender-lx8s.onrender.com/search"
# SEARCH_ENDPOINT = "http://127.0.0.1:8000/search"

st.title("SHL Assessment Recommendation System")

def display_result(response):
    """
    Display the search results in a table format.
    """
    hits = json.loads(response.content.decode())
    COLUMNS_ORDER = ["Name", "URL", "Remote_Testing" , "Adaptive_IRT", "Test_Type", "Description", "Assessment_Time"]
    df = pd.DataFrame([hit["fields"] for hit in hits])
    df = df.loc[:, COLUMNS_ORDER]

    ## Wrting results
    def make_clickable(row):
        return f'<a target="_blank" href={row['URL']}>{row['Name']}</a>'

    df['Name'] = df.apply(make_clickable, axis=1)
    df = df.drop(["URL", "Description"], axis=1)
    df.columns = ["Name", "Remote Testing", "Adaptive/IRT", "Test Type", "Assessment Time (min)"]
    st.write(df.to_html(escape=False, index=False, justify="left"), unsafe_allow_html=True)

with st.form("my-form"):
   query = st.text_area("Enter a query or job description or URL")
   submit_button = st.form_submit_button("Submit")

if submit_button:
    start_time = time.time()
    response = requests.get(SEARCH_ENDPOINT, params={"query": query})
    st.write(f"Query time: {time.time() - start_time:.2f} seconds")
    if response.status_code == 200:
        display_result(response)
    else: 
        st.error(f"Status Code: {response.status_code}\n{response.content.decode()}")
        


