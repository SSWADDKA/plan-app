import streamlit as st
import google.generativeai as genai
from docxtpl import DocxTemplate
import io

# --- 1. การตั้งค่าหน้าจอ (Wide Mode) ---
st.set_page_config(layout="wide", page_title="PLAN - ระบบช่วยเขียนแผนการสอน")

# ตกแต่ง UI ด้วย CSS ให้ใกล้เคียงกับรูปตัวอย่าง
st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .stSidebar { background-color: #ffffff; border-right: 1px solid #e0e0e0; }
    .stButton>button { 
        width: 100%; 
        border-radius: 8px; 
        height: 3em; 
        background-color: #8faadc; 
        color: white; 
        font-weight: bold;
        border: none;
    }
    .stDownloadButton>button {
        background-color: #2c3e50;
        color: white;
    }
    .preview-box {
        border: 1px solid #d1d1d1;
        padding: 20px;
        border-radius: 5px;
        background-color: white;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. การเชื่อมต่อ API ---
# ดึง Key จาก Streamlit Secrets เพื่อความปลอดภัย
GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash') # ใช้รุ่นล่าสุดที่คุณมีสิทธิ์

# --- 3. ส่วนของ SIDEBAR (แถบซ้ายสำหรับกรอกข้อมูล) ---
with st.sidebar:
    st.markdown("### 📝 สร้างแผนการสอน")
    st.caption("กรอกข้อมูลเพื่อให้ AI ช่วยร่างแผนการสอน")
    
    with st.form("input_form"):
        col1, col2 = st.columns(2)
        with col1:
            subject = st.text_input("วิชา", placeholder="เช่น วิทยาศาสตร์")
            teacher_name = st.text_input("ชื่อครูผู้สอน")
        with col2:
            grade = st.text_input("ระดับชั้น", placeholder="เช่น ม.5")
            time = st.selectbox("เวลา (นาที)", ["60 นาที", "120 นาที", "อื่น ๆ"])
            
        topic = st.text_input("หัวข้อ / สาระสำคัญ", placeholder="เช่น Lego Mindstorms EV3")
        context_input = st.text_area("บริบทโรงเรียน/นักเรียน", placeholder="เช่น เน้น Active Learning, มีอุปกรณ์ครบ")
        skills = st.text_area("ทักษะที่ต้องการพัฒนา (K-P-A)", placeholder="เช่น การแก้ปัญหา, การเขียนโค้ด")
        
        submitted = st.form_submit_button("✨ สร้างแผนการสอน")

# --- 4. ส่วนของ MAIN CONTENT (แสดงผลทางขวา) ---
if not submitted and 'ai_result' not in st.session_state:
    # หน้าต้อนรับตอนยังไม่ได้กดปุ่ม
    st.write("")
    st.write("")
    st.write("")
    st.columns([1, 2, 1])[1].info("📝 รอการสร้างแผนการสอน: กรอกข้อมูลทางซ้ายมือแล้วกดปุ่มเพื่อเริ่มร่างแผน")

if submitted:
    with st.spinner('AI กำลังออกแบบแผนการสอนให้คุณ...'):
        # สร้าง Prompt แบบละเอียดเพื่อให้ได้แผนที่ตรงใจ
        prompt = f"""
        จงเขียนแผนการสอนภาษาไทยระดับมืออาชีพ
        วิชา: {subject}
        ระดับชั้น: {grade}
        หัวข้อ: {topic}
        เวลา: {time}
        บริบทพิเศษ: {context_input}
        เน้นทักษะ: {skills}
        
        โครงสร้างแผน:
        1. สาระสำคัญ (Concept)
        2. จุดประสงค์การเรียนรู้ (K-P-A)
        3. กิจกรรมการเรียนรู้ (ใช้โมเดล 5E หรือการสอนเชิงปฏิบัติ)
        4. การวัดและประเมินผล
        """
        response = model.generate_content(prompt)
        
        # เก็บค่าเข้า SessionState
        st.session_state['ai_result'] = response.text
        st.session_state['teacher_name'] = teacher_name
        st.session_state['subject'] = subject
        st.session_state['topic'] = topic

# ส่วนแสดงผล Preview และการแก้ไข
if 'ai_result' in st.session_state:
    # ส่วนหัวของ Preview
    prev_col1, prev_col2 = st.columns([7, 3])
    with prev_col1:
        st.markdown("#### Preview Mode | A4 Document View")
    
    with prev_col2:
        # ระบบ Export Word (ต้องมีไฟล์ template.docx บน GitHub)
        try:
            doc = DocxTemplate("template.docx")
            context_to_export = {
                'teacher_name': st.session_state['teacher_name'],
                'subject': st.session_state['subject'],
                'topic': st.session_state['topic'],
                'ai_content': st.session_state['ai_result']
            }
            doc.render(context_to_export)
            
            bio = io.BytesIO()
            doc.save(bio)
            
            st.download_button(
                label="🖨️ Print / Download Word",
                data=bio.getvalue(),
                file_name=f"Plan_{st.session_state['topic']}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
        except:
            st.warning("⚠️ อย่าลืมอัปโหลดไฟล์ template.docx ขึ้น GitHub")

    # กล่อง Text Area สำหรับแก้ไขเนื้อหา
    edited_content = st.text_area(
        "เนื้อหาแผนการสอน (คุณสามารถปรับปรุงได้ที่นี่):", 
        value=st.session_state['ai_result'], 
        height=500
    )
    # อัปเดตข้อมูลเมื่อมีการแก้
    st.session_state['ai_result'] = edited_content