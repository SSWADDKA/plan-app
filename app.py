import streamlit as st
import google.generativeai as genai
from docxtpl import DocxTemplate
import io

# --- 1. ตั้งค่า API (เอารหัสคุณมาใส่ตรงนี้) ---
GOOGLE_API_KEY = "..."
GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
model = genai.GenerativeModel('gemini-2.5-flash')

# --- 2. หน้าจอแอป ---
st.title("🤖 PLAN: ผู้ช่วยสร้างแผนการสอน")

# ฟอร์มรับข้อมูล
with st.form("my_form"):
    teacher_name = st.text_input("ชื่อครูผู้สอน")
    subject = st.text_input("วิชา")
    topic = st.text_input("เรื่องที่จะสอน")
    submitted = st.form_submit_button("✨ ให้ AI ช่วยคิด")

# --- 3. ส่วนประมวลผล (เมื่อกดปุ่ม) ---
if submitted:
    with st.spinner('AI กำลังทำงาน...'):
        # สั่ง Gemini
        prompt = f"ช่วยเขียนแผนการสอนวิชา {subject} เรื่อง {topic} แบบสั้นๆ เข้าใจง่าย"
        response = model.generate_content(prompt)
        
        # เก็บผลลัพธ์ไว้ใน Session (เพื่อให้แก้ไขได้)
        st.session_state['ai_result'] = response.text
        st.session_state['teacher_name'] = teacher_name
        st.session_state['subject'] = subject

# --- 4. ส่วนแสดงผลและแก้ไข ---
if 'ai_result' in st.session_state:
    st.success("เสร็จเรียบร้อย!")
    
    # กล่องข้อความที่แก้ไขได้
    edited_text = st.text_area("แก้ไขเนื้อหาตรงนี้ได้เลย:", 
                               value=st.session_state['ai_result'], 
                               height=200)
    
    # --- 5. ปุ่ม Export Word ---
    # โหลด Template
    doc = DocxTemplate("template.docx")
    
    # เอาข้อมูลไปแทนที่ใน Template
    context = {
        'teacher_name': st.session_state['teacher_name'],
        'subject': st.session_state['subject'],
        'ai_content': edited_text
    }
    doc.render(context)
    
    # แปลงไฟล์เพื่อดาวน์โหลด
    bio = io.BytesIO()
    doc.save(bio)
    
    st.download_button(
        label="📄 ดาวน์โหลดไฟล์ Word",
        data=bio.getvalue(),
        file_name=f"Plan_{st.session_state['subject']}.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )