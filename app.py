import streamlit as st
import google.generativeai as genai
from docxtpl import DocxTemplate
import io
import re

# --- 1. ข้อมูลวิชาและ KPA ---
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

# --- 2. การตกแต่ง UI (Azure Blue Theme) ---
st.set_page_config(layout="wide", page_title="PLAN - ระบบช่วยเขียนแผนการสอน")

st.markdown("""
    <style>
    .stApp { background-color: #f0f7ff; }
    [data-testid="stSidebar"] { width: 480px !important; background-color: #ffffff; border-right: 4px solid #3498db; }
    .paper-page {
        background-color: white; padding: 50px 75px; border: 1px solid #d1d1d1;
        box-shadow: 0 15px 35px rgba(52, 152, 219, 0.1); color: #2c3e50; line-height: 1.8;
        border-top: 10px solid #3498db; border-radius: 4px;
    }
    .plan-header { text-align: center; border-bottom: 2px solid #3498db; margin-bottom: 30px; padding-bottom: 10px; }
    div.stButton > button { 
        width: 100%; border-radius: 12px; height: 3.5em; background-color: #3498db; color: #fff; font-weight: bold; border: none;
    }
    div.stButton > button:hover { background-color: #2980b9; }
    
    /* สไตล์ตารางในหน้า Preview */
    table { width: 100%; border-collapse: collapse; margin: 15px 0; }
    th { background-color: #ebf5fb; color: #2980b9; border: 1px solid #3498db; padding: 10px; text-align: center; }
    td { border: 1px solid #ddd; padding: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. ฟังก์ชัน Clean ข้อมูล ---
def clean_text(text):
    return re.sub(r'[#*_]{1,3}', '', text).strip()

# --- 4. การเชื่อมต่อ API ---
GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

# --- 5. SIDEBAR: รับข้อมูล ---
with st.sidebar:
    st.title("💙 PLAN AI Teacher")
    with st.form("input_form"):
        school = st.text_input("โรงเรียน")
        teacher = st.text_input("ชื่อครูผู้สอน")
        term = st.text_input("ภาคเรียน/ปีการศึกษา", value="1 / 2567")
        grade_level = st.selectbox("ระดับการศึกษา", list(SUBJECTS_DATA.keys()))
        subject_name = st.selectbox("วิชา", SUBJECTS_DATA[grade_level])
        
        col1, col2 = st.columns(2)
        with col1:
            code = st.text_input("รหัสวิชา")
            grade = st.text_input("ชั้นปี")
        with col2:
            time_hours = st.text_input("เวลา (ชั่วโมง)", value="2")
            
        topic = st.text_input("หัวข้อบทเรียน")
        extra_skills = st.text_area("ทักษะที่ต้องการเน้นพิเศษ")
        sel_k = st.multiselect("ด้าน K", KPA_OPTIONS["K (Knowledge)"])
        sel_p = st.multiselect("ด้าน P", KPA_OPTIONS["P (Process)"])
        sel_a = st.multiselect("ด้าน A", KPA_OPTIONS["A (Attitude)"])
        
        submitted = st.form_submit_button("🚀 สร้างแผนการสอน")

# --- 6. ประมวลผล ---
if submitted:
    with st.spinner('AI กำลังร่างแผนการสอน...'):
        prompt = f"""
        จงเขียนแผนการจัดการเรียนรู้ภาษาไทยโดยละเอียดสำหรับ วิชา {subject_name} ({code}) เรื่อง {topic} ชั้น {grade} 
        ห้ามใช้สัญลักษณ์ตกแต่งเยอะ ให้เน้นเนื้อหาที่ครบถ้วนตามหัวข้อ:
        1. มาตรฐานการเรียนรู้ 2. สาระสำคัญ 3. จุดประสงค์ KPA 4. กิจกรรมการเรียนรู้ 5. สื่อ 6. การประเมินผล
        
        และสำคัญมาก: ในส่วน 'ตารางเกณฑ์การประเมินรูบริกส์' ให้เขียนเนื้อหาแยกเป็นข้อๆ 
        โดยระบุระดับ ดีเยี่ยม, ดี, พอใช้, ปรับปรุง ให้ชัดเจน เพื่อให้นำไปวางในตารางได้
        """
        response = model.generate_content(prompt)
        
        st.session_state['ai_raw'] = response.text
        st.session_state['data_context'] = {
            'school': school, 'teacher': teacher, 'term': term,
            'subject': subject_name, 'code': code, 'grade': grade,
            'topic': topic, 'time': time_hours
        }

# --- 7. แสดงผลและ Export ---
if 'ai_raw' in st.session_state and 'data_context' in st.session_state:
    data = st.session_state['data_context']
    
    with st.columns([8, 2])[1]:
        try:
            doc = DocxTemplate("template.docx")
            # Clean ข้อมูลก่อนส่งเข้า Word
            clean_ai = clean_text(st.session_state['ai_raw'])
            
            # เตรียมข้อมูลส่งเข้า Template
            # ตัวแปร ai_content ใน Word จะถูกตั้งเป็นฟอนต์ 16 ปกติ
            final_context = {**data, 'ai_content': clean_ai, 'rubric_table': clean_ai} 
            
            doc.render(final_data)
            bio = io.BytesIO()
            doc.save(bio)
            st.download_button("📘 โหลดไฟล์ Word", bio.getvalue(), f"แผน_{data['topic']}.docx")
        except:
            st.warning("⚠️ โปรดอัปโหลด template.docx และเช็คชื่อตัวแปร")

    # หน้า Preview
    st.markdown('<div class="paper-page">', unsafe_allow_html=True)
    st.markdown(f"""
        <div class="plan-header">
            <h3>บันทึกการจัดการเรียนรู้</h3>
            <p style="color: #2980b9;"><b>{data['school']}</b></p>
            <p>รหัส {data['code']} วิชา {data['subject']} ชั้น {data['grade']} เวลา {data['time']} ชม.</p>
            <p>ผู้สอน: {data['teacher']}</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown(clean_text(st.session_state['ai_raw']))
    st.markdown('</div>', unsafe_allow_html=True)