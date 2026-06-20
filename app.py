import streamlit as st
import http.client
import json

# Paste your free Gemini API Key inside the quotes below
API_KEY = "AQ.Ab8RN6LqXdpQZRZLUu_TF1WhGHc__fv_UnDGsmJRFhtUos5pkw"

# 1. Set up the sleek dark web page layout
st.set_page_config(page_title="IELTS AI Tutor", page_icon="🎓", layout="centered")

st.title("🎓 IELTS AI TUTOR")
st.subheader("Sandbox Engine — V1.0")
st.write("Paste your essay below for an official examiner breakdown.")

# 2. Create the user text box input
essay = st.text_area("Your IELTS Essay:", height=250, placeholder="Type or paste your essay here...")

# 3. Create the analyze button
if st.button("⚡ Analyze Essay"):
    if not essay.strip():
        st.warning("Please paste an essay first!")
    else:
        system_prompt = "You are a strict IELTS examiner. Give an overall band score (1-9) and clear bullet points of feedback."
        payload = {
            "contents": [{"parts": [{"text": f"{system_prompt}\n\nEssay:\n{essay}"}]}]
        }

        # Connect to the backend network
        conn = http.client.HTTPSConnection("generativelanguage.googleapis.com")
        headers = {"Content-Type": "application/json"}
        url = f"/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY}"

        # Show a loading spinner while processing
        with st.spinner("Connecting to Gemini... Analyzing your essay..."):
            try:
                conn.request("POST", url, body=json.dumps(payload), headers=headers)
                response = conn.getresponse()
                res_data = json.loads(response.read().decode("utf-8"))
                
                if response.status == 200:
                    feedback = res_data["candidates"][0]["content"]["parts"][0]["text"]
                    
                    # 4. Display the results beautifully on the page
                    st.success("Analysis Complete!")
                    st.markdown("### === EXAMINER FEEDBACK ===")
                    st.write(feedback)
                else:
                    st.error(f"Server error: {res_data.get('error', {}).get('message', 'Unknown Error')}")
            except Exception as e:
                st.error(f"Something went wrong. Error: {e}")
            finally:
                conn.close()