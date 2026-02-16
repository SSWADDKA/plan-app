import streamlit as st
import google.generativeai as genai
from docxtpl import DocxTemplate
import io
import json

# --- 1. การตั้งค่าหน้าจอและสไตล์ ---
st.set_page_config(layout="wide", page_title="PLAN - ระบบช่วยเขียนแผนการสอน")

st.markdown("""
    <style>
    .stApp { background-color: #fcfcfc; }
    [data-testid="stSidebar"] { width: 450px !important; background-color: #ffffff; border-right: 1px solid #eee; }
    
    /* สไตล์กระดาษแผนการสอน (Layer 1) */
    .paper-container {
        background-color: #ffffff;
        padding: 45px 60px;
        border: 1px solid #e0e0e0;
        box-shadow: 0 10px 30px rgba(0,0,0,0.05);
        border-radius: 4px;
        color: #000000;
        margin-top: 20px;
    }

    div.stButton > button {
        width: 100%;
        border-radius: 8px;
        height: 3.5em;
        background-color: #000000;
        color: #ffffff;
        font-weight: bold;
        border: none;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }

    .stTextArea textarea {
        border: 1px solid #eee !important;
        background-color: #fdfdfd !important;
        font-size: 16px !important;
        line-height: 1.7 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. การเชื่อมต่อ API ---
GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

# --- 3. SIDEBAR (ส่วนกรอกข้อมูลตามแบบฟอร์มจริง) ---
with st.sidebar:
    st.markdown("### 📝 ข้อมูลแผนการจัดการเรียนรู้")
    with st.form("input_form"):
        school_name = st.text_input("โรงเรียน", placeholder="ระบุชื่อโรงเรียน")
        teacher_name = st.text_input("ชื่อครูผู้สอน")
        
        col1, col2 = st.columns(2)
        with col1:
            subject = st.text_input("วิชา", placeholder="เช่น หุ่นยนต์")
            grade = st.text_input("ชั้น ม.", placeholder="5")
        with col2:
            topic = st.text_input("เรื่อง", placeholder="เช่น เซนเซอร์ EV3")
            duration = st.text_input("เวลา (ชั่วโมง)", placeholder="2")
            
        context_input = st.text_area("บริบทนักเรียน/ทักษะที่เน้น (K-P-A)", height=100)
        
        submitted = st.form_submit_button("🚀 สร้างแผนการสอน")

# --- 4. ส่วนแสดงผลหลัก (MAIN CONTENT) ---
if submitted:
    with st.spinner('AI กำลังร่างแผนตามแบบฟอร์มมาตรฐาน...'):
        # สั่ง AI ให้ตอบกลับเป็นโครงสร้างที่ชัดเจน
        prompt = f"""
        เขียนแผนการจัดการเรียนรู้ภาษาไทยสำหรับ วิชา: {subject} เรื่อง: {topic} ชั้น: {grade}
        บริบทเพิ่มเติม: {context_input}
        
        จงเขียนเนื้อหาแยกตามหัวข้อดังนี้ (ห้ามเขียนรวมกัน):
        [STANDARDS]: มาตรฐานการเรียนรู้และตัวชี้วัดที่เกี่ยวข้อง
        [CONCEPT]: สาระสำคัญของบทเรียนนี้
        [OBJECTIVES]: จุดประสงค์การเรียนรู้ (แยกด้าน K, P, A)
        [ACTIVITIES]: ขั้นตอนการสอน (ขั้นนำ, สอน, สรุป)
        [RESOURCES]: สื่อและแหล่งเรียนรู้
        [EVALUATION]: วิธีการวัดและประเมินผล
        """
        response = model.generate_content(prompt)
        full_text = response.text
        
        # ฟังก์ชันช่วยแยกเนื้อหามาใส่ตัวแปร
        def get_section(tag, text):
            try:
                start = text.find(f"[{tag}]") + len(tag) + 2
                end = text.find("[", start)
                return text[start:end].strip() if end != -1 else text[start:].strip()
            except: return ""

        # เก็บข้อมูลลง Session
        st.session_state['plan_data'] = {
            'school_name': school_name,
            'teacher_name': teacher_name,
            'subject': subject,
            'grade': grade,
            'topic': topic,
            'duration': duration,
            'standards': get_section("STANDARDS", full_text),
            'concept': get_section("CONCEPT", full_text),
            'objectives': get_section("OBJECTIVES", full_text),
            'activities': get_section("ACTIVITIES", full_text),
            'resources': get_section("RESOURCES", full_text),
            'evaluation': get_section("EVALUATION", full_text),
            'full_display': full_text # สำหรับโชว์ในหน้าเว็บ
        }

if 'plan_data' in st.session_state:
    data = st.session_state['plan_data']
    
    # ปุ่มดาวน์โหลด
    col_title, col_btn = st.columns([7, 3])
    with col_btn:
        try:
            doc = DocxTemplate("template.docx")
            doc.render(data)
            bio = io.BytesIO()
            doc.save(bio)
            st.download_button("📥 ดาวน์โหลดไฟล์ Word (.docx)", bio.getvalue(), f"แผนการสอน_{data['topic']}.docx")
        except:
            st.warning("⚠️ อย่าลืมใส่รหัส {{...}} ในไฟล์ template.docx และอัปโหลดขึ้น GitHub")

    # ส่วนแสดงผลบนหน้าเว็บ (Paper View)
    st.markdown('<div class="paper-container">', unsafe_allow_html=True)
    st.markdown(f"<h2 style='text-align:center;'>แผนการจัดการเรียนรู้</h2>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align:center;'><b>โรงเรียน:</b> {data['school_name']} | <b>วิชา:</b> {data['subject']} | <b>เรื่อง:</b> {data['topic']}</p>", unsafe_allow_html=True)
    
    # ส่วนแก้ไขเนื้อหา (คลิกแก้ได้เลย)
    edited_text = st.text_area("เนื้อหาแผนการสอน (แก้ไขได้ที่นี่):", value=data['full_display'], height=800)
    
    # หากมีการแก้ไข ให้พยายามอัปเดตข้อมูลที่จะ Export ด้วย (แบบคร่าวๆ)
    if edited_text != data['full_display']:
        st.session_state['plan_data']['full_display'] = edited_text
        st.session_state['plan_data']['activities'] = edited_text # บันทึกเนื้อหาที่แก้ลงกิจกรรมเป็นหลัก
        
    st.markdown('</div>', unsafe_allow_html=True)