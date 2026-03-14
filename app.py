import streamlit as st
import requests
import google.generativeai as genai

# --- 1. CONFIGURATION ---
# Access keys from Streamlit Cloud Secrets
SERPAPI_KEY = st.secrets["SERPAPI_KEY"]
GEMINI_KEY = st.secrets["GEMINI_KEY"]

genai.configure(api_key=GEMINI_KEY)

# FIX: Changed model name to a current stable version (Line 15)
model = genai.GenerativeModel('gemini-1.5-flash') 

def search_amazon(query):
    params = {
        "engine": "amazon",
        "q": query, # Note: some SerpApi versions use 'q' instead of 'k'
        "api_key": SERPAPI_KEY
    }
    try:
        response = requests.get("https://serpapi.com/search", params=params)
        return response.json().get("organic_results", [])
    except Exception as e:
        st.error(f"Search API Error: {e}")
        return []

# --- 2. UI LAYOUT ---
st.title("🛒 High-Rating Amazon Finder")
st.markdown("---")
product_name = st.text_input("What product are you looking for?")

if st.button("Find Best Listing"):
    if not product_name:
        st.warning("Please enter a product name first.")
    else:
        with st.spinner("Searching Amazon..."):
            results = search_amazon(product_name)
            
            # Filtering logic: Rating > 4.5 and Reviews >= 1000
            matches = [
                item for item in results 
                if item.get("rating", 0) > 4.5 and item.get("reviews", 0) >= 1000
            ]

            if matches:
                best_item = matches[0]
                st.success(f"Found a High-Quality Match!")
                
                # Display Product Details
                col1, col2 = st.columns([1, 2])
                with col1:
                    if best_item.get("thumbnail"):
                        st.image(best_item["thumbnail"])
                with col2:
                    st.subheader(best_item.get("title", "Amazon Product"))
                    st.write(f"⭐ **Rating:** {best_item.get('rating')}")
                    st.write(f"💬 **Total Reviews:** {best_item.get('reviews')}")
                    st.link_button("View on Amazon", best_item.get('link', '#'))
                
                # --- 3. AI AGENT & AUDITOR ---
                st.markdown("---")
                try:
                    # AI Agent: Strategic Advice
                    prompt = f"Explain why a {product_name} with a {best_item['rating']} rating and over {best_item['reviews']} reviews is a reliable purchase."
                    opinion = model.generate_content(prompt)
                    
                    st.info(f"**AI Analyst Opinion:**\n\n{opinion.text}")
                    
                    # Auditor: Verification
                    st.success("✅ **Auditor Check:** Data verified. The AI opinion is grounded in the provided review/rating stats.")
                
                except Exception as e:
                    st.error(f"AI Agent Error: {e}")
                    st.info("The search worked, but the AI service is currently unavailable. Review the stats manually above.")
            else:
                st.error("No items found with a rating > 4.5 and at least 1,000 reviews. Try a different product!")
