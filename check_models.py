import google.generativeai as genai

# --- ใส่ API KEY ของคุณตรงนี้ ---
GOOGLE_API_KEY = "AIzaSyBB1_SLo-MDxDmwU3wlJSAre9JYdXAff54"
genai.configure(api_key=GOOGLE_API_KEY)

print("กำลังค้นหา Model ที่ใช้ได้...")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"- {m.name}")
except Exception as e:
    print(f"เกิดข้อผิดพลาด: {e}")