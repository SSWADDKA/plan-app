import streamlit as st
import google.generativeai as genai
from docxtpl import DocxTemplate
import io
import re

# --- 1. ข้อมูลพื้นฐาน ---
SUBJECTS_DATA = {
    "ประถมศึกษา": ["ภาษาไทย", "คณิตศาสตร์", "วิทยาศาสตร์และเทคโนโลยี", "สังคมศึกษาฯ", "สุขศึกษาฯ", "ศิลปะ", "การงานอาชีพ", "ภาษาอังกฤษ"],
    "มัธยมศึกษาตอนต้น": ["ภาษาไทยพื้นฐาน", "คณิตศาสตร์พื้นฐาน", "วิทยาศาสตร์พื้นฐาน", "วิทยาการคำนวณ", "สังคมศึกษาฯ", "ประวัติศาสตร์", "สุขศึกษา", "พลศึกษา", "ศิลปะ", "การงานอาชีพ", "ภาษาอังกฤษพื้นฐาน"],
    "มัธยมศึกษาตอนปลาย": ["ภาษาไทยพื้นฐาน", "คณิตศาสตร์พื้นฐาน", "คณิตศาสตร์เพิ่มเติม", "ฟิสิกส์", "เคมี", "ชีววิทยา", "โลกและอวกาศ", "สังคมศึกษาฯ", "ประวัติศาสตร์", "สุขศึกษา", "พลศึกษา", "ศิลปะ", "การงานอาชีพ", "ภาษาอังกฤษพื้นฐาน", "ภาษาอังกฤษเพิ่มเติม", "วิทยาการคำนวณ", "การออกแบบและเทคโนโลยี"]
}

KPA_OPTIONS = {
    "K (Knowledge)": ["ความรู้ความเข้าใจ", "การอธิบายหลักการ", "ความเข้าใจเนื้อหา"],
    "P (Process)": ["ทักษะการปฏิบัติ", "ทักษะการคิดวิเคราะห์", "ทักษะการทำงานกลุ่ม"],
    "A (Attitude)": ["ใฝ่เรียนรู้", "มุ่งมั่นในการทำงาน", "มีวินัย"]
}

# --- 2. การตั้งค่า UI (Blue Theme) ---
st.set_page_config(layout="wide", page_title="PLAN - ระบบช่วยเขียนแผนการสอน")

st.markdown("""
    <style>
    .stApp { background-color: #eef2f7; }
    [data-testid="stSidebar"] { width: 480px !important; background-color: #ffffff; border-right: 3px solid #3498db; }
    .paper-page {
        background-color: white; padding: 60px 80px; border: 1px solid #d1d1d1;
        box-shadow: 0 15px 35px rgba(52, 152, 219, 0.15); color: #2c3e50; line-height: 1.8;
        border-top: 10px solid #3498db; border-radius: 5px;
    }
    .plan-header { text-align: center; border-bottom: 2px solid #3498db; margin-bottom: 30px; padding-bottom: 15px; }
    .plan-header h3 { color: #2980b9; font-weight: bold; }
    div.stButton > button { 
        width: 100%; border-radius: 12px; height: 3.8em; background-color: #3498db; color: #fff; font-weight: bold; border: none;
        transition: 0.3s; box-shadow: 0 4px 6px rgba(52, 152, 219, 0.3);
    }
    div.stButton > button:hover { background-color: #2980b9; transform: translateY(-2px); }
    .section-title { color: #2980b9; font-weight: bold; font-size: 1.2em; margin-top: 1em; }
    </style>
    """, unsafe_allow_html=True)

def clean_for_preview(text):
    text = re.sub(r'[#*_]{1,3}', '', text)
    return text.strip()

# --- 3. การเชื่อมต่อ API ---
GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

# --- 4. SIDEBAR ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3534/3534033.png", width=80)
    st.title("💙 PLAN AI Teacher")
    
    with st.form("input_form"):
        school = st.text_input("📍 โรงเรียน")
        teacher = st.text_input("👨‍🏫 ชื่อครูผู้สอน")
        term = st.text_input("📅 ภาคเรียน/ปีการศึกษา", value="1 / 2567")
        grade_level = st.selectbox("🎓 ระดับการศึกษา", list(SUBJECTS_DATA.keys()))
        subject = st.selectbox("📚 วิชา", SUBJECTS_DATA[grade_level])
        
        col1, col2 = st.columns(2)
        with col1:
            code = st.text_input("🔢 รหัสวิชา")
            grade = st.text_input("🏫 ชั้นปี")
        with col2:
            time = st.text_input("⏳ เวลา (ชั่วโมง)", value="2")
            
        topic = st.text_input("💡 หัวข้อบทเรียน")
        extra_skills = st.text_area("🎯 ทักษะพิเศษ", height=70)
        sel_k = st.multiselect("Knowledge (K)", KPA_OPTIONS["K (Knowledge)"])
        sel_p = st.multiselect("Process (P)", KPA_OPTIONS["P (Process)"])
        sel_a = st.multiselect("Attitude (A)", KPA_OPTIONS["A (Attitude)"])
        
        submitted = st.form_submit_button("🚀 เริ่มสร้างแผนการสอน")

# --- 5. ประมวลผล ---
if submitted:
    with st.spinner('💎 AI กำลังออกแบบแผนการสอนสีฟ้าให้คุณ...'):
        prompt = f"""เขียนแผนการสอนเรื่อง {topic} วิชา {subject} ({code}) ชั้น {grade} เน้นทักษะ {extra_skills} จุดประสงค์ KPA: {sel_k}, {sel_p}, {sel_a} โครงสร้าง: มาตรฐานการเรียนรู้, สาระสำคัญ, จุดประสงค์, กิจกรรม (Active Learning), สื่อ, และตารางรูบริกส์ (Markdown Table) ห้ามใช้สัญลักษณ์ตกแต่งเยอะ"""
        response = model.generate_content(prompt)
        
        # สร้างข้อมูลทั้งสองอย่างพร้อมกันเพื่อป้องกัน KeyError
        st.session_state['ai_raw'] = response.text
        st.session_state['data_context'] = {
            'school': school, 'teacher': teacher, 'term': term,
            'subject': subject, 'code': code, 'grade': grade,
            'topic': topic, 'time': time
        }

# --- 6. แสดงผล (แก้ไขส่วนป้องกัน Error) ---
if 'ai_raw' in st.session_state and 'data_context' in st.session_state:
    doc_data = st.session_state['data_context']
    
    c1, c2 = st.columns([8, 2])
    with c2:
        try:
            doc = DocxTemplate("template.docx")
            final_data = {**doc_data, 'ai_content': clean_for_preview(st.session_state['ai_raw'])}
            doc.render(final_data)
            bio = io.BytesIO()
            doc.save(bio)
            st.download_button("📘 ดาวน์โหลดไฟล์ Word", bio.getvalue(), f"แผน_{doc_data['topic']}.docx")
        except: 
            st.warning("⚠️ โปรดอัปโหลด template.docx")

    st.markdown('<div class="paper-page">', unsafe_allow_html=True)
    st.markdown(f"""
        <div class="plan-header">
            <h3>บันทึกการจัดการเรียนรู้</h3>
            <p style="font-size: 1.2em; color: #2980b9;"><b>{doc_data['school']}</b></p>
            <p>ภาคเรียนที่ {doc_data['term']}</p>
            <p><b>หน่วยการเรียนรู้เรื่อง:</b> {doc_data['topic']}</p>
            <p>รหัสวิชา {doc_data['code']} วิชา {doc_data['subject']} ชั้น {doc_data['grade']} เวลา {doc_data['time']} ชั่วโมง</p>
            <p><b>ผู้สอน:</b> {doc_data['teacher']}</p>
        </div>
    """, unsafe_allow_html=True)

    preview_text = clean_for_preview(st.session_state['ai_raw'])
    st.markdown(preview_text)
    
    with st.expander("🛠️ ปรับแต่งเนื้อหาเพิ่มเติม"):
        st.session_state['ai_raw'] = st.text_area("แก้ไขโค้ดแผน:", value=st.session_state['ai_raw'], height=400)
    st.markdown('</div>', unsafe_allow_html=True)
else:
    # หากยังไม่มีการสร้างข้อมูล ให้โชว์คำแนะนำแทนที่จะขึ้น Error
    st.info("👋 ยินดีต้อนรับสู่ระบบ PLAN! กรุณากรอกข้อมูลในแถบด้านซ้ายแล้วกด 'เริ่มสร้างแผนการสอน' เพื่อเริ่มต้นครับ")