import streamlit as st
import google.generativeai as genai
from docxtpl import DocxTemplate
import io

# --- 1. การตั้งค่าหน้าจอและสไตล์ (ฉบับ Minimal White & Layer) ---
st.set_page_config(layout="wide", page_title="PLAN - ผู้ช่วยออกแบบการสอน")

st.markdown("""
    <style>
    /* 1. พื้นหลังหลัก (Layer 0) */
    .stApp {
        background-color: #fcfcfc;
    }

    /* 2. Sidebar สีขาวสะอาด */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #eeeeee;
    }

    /* 3. ตกแต่ง Input และ Textarea ให้มีขอบนวล */
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
        border-radius: 8px !important;
        border: 1px solid #e0e0e0 !important;
        background-color: #ffffff !important;
        color: #000000 !important;
    }

    /* 4. ปุ่มกดสีดำ (คมเข้ม มีมิติ) */
    div.stButton > button {
        width: 100%;
        border-radius: 8px;
        height: 3.2em;
        background-color: #000000;
        color: #ffffff;
        font-weight: 500;
        border: none;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    div.stButton > button:hover {
        background-color: #333333;
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
        transform: translateY(-2px);
    }

    /* 5. ส่วน Preview ให้ดูเหมือนกระดาษลอยขึ้นมา (Layer 1) */
    .stTextArea textarea {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 1px solid #e0e0e0 !important;
        box-shadow: 0 10px 30px rgba(0,0,0,0.06) !important;
        padding: 25px !important;
        line-height: 1.8 !important;
        font-family: 'Sarabun', sans-serif;
    }

    /* 6. ปุ่ม Download สไตล์ Outline */
    .stDownloadButton > button {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 1px solid #000000 !important;
        border-radius: 8px !important;
        font-weight: bold;
        transition: all 0.3s;
    }
    .stDownloadButton > button:hover {
        background-color: #000000 !important;
        color: #ffffff !important;
    }

    /* ปรับแต่งหัวข้อ */
    h1, h2, h3, h4, h5, p, span {
        color: #000000 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. การเชื่อมต่อ API (ดึงจาก Secrets) ---
try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=GOOGLE_API_KEY)
    # ใช้รุ่น Gemini 2.5 Flash ตามโควตาที่คุณได้รับ
    model = genai.GenerativeModel('gemini-2.5-flash')
except Exception as e:
    st.error("กรุณาตั้งค่า GOOGLE_API_KEY ใน Streamlit Secrets ก่อนใช้งาน")

# --- 3. ส่วน SIDEBAR (ข้อมูลการสอน) ---
with st.sidebar:
    st.markdown("### 📝 สร้างแผนการสอน")
    st.caption("AI จะช่วยร่างแผนการสอนที่เหมาะสมกับบริบทของคุณ")
    
    with st.form("input_form"):
        col1, col2 = st.columns(2)
        with col1:
            subject = st.text_input("วิชา", placeholder="เช่น วิทยาการคำนวณ")
            teacher_name = st.text_input("ชื่อครูผู้สอน")
        with col2:
            grade = st.text_input("ระดับชั้น", placeholder="เช่น ม.5")
            time = st.selectbox("เวลา", ["60 นาที", "120 นาที", "อื่น ๆ"])
            
        topic = st.text_input("หัวข้อการเรียนรู้", placeholder="เช่น Lego Mindstorms EV3")
        context_input = st.text_area("บริบท (นักเรียน/อุปกรณ์)", placeholder="เช่น นักเรียนเน้นปฏิบัติ, อุปกรณ์ครบ")
        skills = st.text_area("ทักษะที่เน้น (K-P-A)", placeholder="เช่น การคิดแก้ปัญหา, การเขียนโค้ด")
        
        submitted = st.form_submit_button("✨ เริ่มร่างแผนการสอน")

# --- 4. ส่วนแสดงผลหลัก (MAIN CONTENT) ---
if not submitted and 'ai_result' not in st.session_state:
    st.write("")
    st.write("")
    st.columns([1, 2, 1])[1].info("📝 กรอกข้อมูลทางซ้ายมือ และกดปุ่มเพื่อเริ่มร่างแผนการสอน")

if submitted:
    with st.spinner('กำลังใช้ AI ออกแบบแผนการสอน...'):
        prompt = f"""
        จงเขียนแผนการสอนวิชา {subject} เรื่อง {topic} สำหรับนักเรียนชั้น {grade} 
        โดยใช้เวลาสอน {time} ภายใต้บริบท: {context_input} 
        เน้นพัฒนาทักษะ: {skills}
        
        โครงสร้างแผนที่ต้องการ:
        1. สาระสำคัญและแนวคิดหลัก
        2. จุดประสงค์การเรียนรู้ (K-P-A)
        3. กิจกรรมการเรียนรู้ (ลำดับขั้นตอนชัดเจน)
        4. สื่อการสอนและแหล่งเรียนรู้
        5. การวัดและประเมินผล
        """
        try:
            response = model.generate_content(prompt)
            # เก็บค่าลง SessionState เพื่อให้แก้ไขได้โดยข้อมูลไม่หาย
            st.session_state['ai_result'] = response.text
            st.session_state['teacher_name'] = teacher_name
            st.session_state['subject'] = subject
            st.session_state['topic'] = topic
        except Exception as e:
            st.error(f"เกิดข้อผิดพลาดในการเรียก AI: {e}")

# ส่วนแสดงผล Preview และปุ่ม Export
if 'ai_result' in st.session_state:
    st.markdown("---")
    header_col1, header_col2 = st.columns([7, 3])
    
    with header_col1:
        st.markdown("#### 📄 มุมมองแผ่นกระดาษ (แก้ไขเนื้อหาได้)")
    
    with header_col2:
        # ระบบ Export Word (ต้องมีไฟล์ template.docx บน GitHub)
        try:
            doc = DocxTemplate("template.docx")
            context_data = {
                'teacher_name': st.session_state['teacher_name'],
                'subject': st.session_state['subject'],
                'topic': st.session_state['topic'],
                'ai_content': st.session_state['ai_result']
            }
            doc.render(context_data)
            
            buffer = io.BytesIO()
            doc.save(buffer)
            
            st.download_button(
                label="📥 ดาวน์โหลดไฟล์ Word (.docx)",
                data=buffer.getvalue(),
                file_name=f"Plan_{st.session_state['topic']}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
        except:
            st.caption("⚠️ หากต้องการดาวน์โหลด กรุณาอัปโหลดไฟล์ template.docx ขึ้น GitHub")

    # ส่วนแก้ไขเนื้อหาที่ AI เจนออกมา (Layer 1)
    edited_text = st.text_area(
        label="เนื้อหาแผนการสอน:",
        value=st.session_state['ai_result'],
        height=650
    )
    # อัปเดตข้อมูลตามที่ผู้ใช้แก้
    st.session_state['ai_result'] = edited_text