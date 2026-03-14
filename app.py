import streamlit as st
import requests
import google.generativeai as genai

# Configuration
SERPAPI_KEY = st.secrets["SERPAPI_KEY"]
GEMINI_KEY = st.secrets["GEMINI_KEY"]

genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-3.1-flash')

def search_amazon(query):
    params = {
        "engine": "amazon",
        "k": query,
        "api_key": SERPAPI_KEY
    }
    response = requests.get("https://serpapi.com/search", params=params)
    return response.json().get("organic_results", [])

st.title("🛒 High-Rating Amazon Finder")
product_name = st.text_input("Enter the product you're looking for:")

if st.button("Find Best Listing"):
    with st.spinner("Searching Amazon..."):
        results = search_amazon(product_name)
        
        # Filtering logic: Rating > 4.5 and Reviews >= 1000
        matches = [
            item for item in results 
            if item.get("rating", 0) > 4.5 and item.get("reviews", 0) >= 1000
        ]

        if matches:
            best_item = matches[0]  # Take the top match
            st.success(f"Found it! {best_item['title']}")
            st.image(best_item.get("thumbnail"))
            st.write(f"⭐ Rating: {best_item['rating']} | 💬 Reviews: {best_item['reviews']}")
            st.link_button("View on Amazon", best_item['link'])
            
            # Use Gemini to give a quick "Expert Opinion"
            opinion = model.generate_content(f"Tell me why a {product_name} with {best_item['reviews']} reviews is a good buy.")
            st.info(f"AI Opinion: {opinion.text}")
        else:
            st.error("Could not find an item matching your high-rating and review requirements.")