import streamlit as st
import json
import os
import random
import time
import pandas as pd  
import requests
from datetime import datetime

# Kiểm tra sự tồn tại của thư viện kết nối API để tránh crash ứng dụng
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False



# Cấu hình giao diện rộng (wide) - Bắt buộc phải nằm ở đầu file Streamlit
st.set_page_config(page_title="PMP & CAPM Exam Prep Portal", page_icon="🎯", layout="wide")
# =========================================================================
# 🎨 TOÀN CỤC: ĐỒNG NHẤT MÀU SIDEBAR (TONE XANH) CHO CẢ LIGHT & DARK MODE
# ==========================================
st.markdown("""
    <style>
    /* 4. Ẩn dòng chữ Made with Streamlit ở dưới chân trang */
    footer {
        visibility: hidden !important;
    }         
    /* ========================================================================= */
    /*  0. KHUNG CHUNG
   ========================================================================= */

.task-card {

    border-radius: 1px;

    padding: 20px;

    margin-bottom: 20px;

    box-shadow: 0 2px 5px rgba(0,0,0,0.05);

    transition: all 0.3s ease;

}

/* =========================================================================
   I. LIGHT MODE
   ========================================================================= */
[data-theme="light"] [data-testid="stSidebar"],

[data-theme="light"] [data-testid="stSidebar"] > div:first-child,

.st-emotion-cache-light [data-testid="stSidebar"],

body[class*="light"] [data-testid="stSidebar"] {
    background-color: #78C8E8 !important;
}

[data-theme="light"] [data-testid="stSidebar"] *,

body[class*="light"] [data-testid="stSidebar"] * {

    color: #0F172A !important;
}
[data-theme="light"] .task-card {

    background-color: #FFFFFF !important;
    color: #333333 !important;
    border: 1px solid #D1D9E0 !important;
}
/* =========================================================================
   II. DARK MODE
   ========================================================================= */

[data-theme="dark"] [data-testid="stSidebar"],

[data-theme="dark"] [data-testid="stSidebar"] > div:first-child,

.st-emotion-cache-dark [data-testid="stSidebar"],

body[class*="dark"] [data-testid="stSidebar"] {

    background-color: #104960 !important;
}
[data-theme="dark"] [data-testid="stSidebar"] *,

body[class*="dark"] [data-testid="stSidebar"] * {

    color: #F8FAFC !important;
}

[data-theme="dark"] .task-card {

    background-color: #04328E !important;

    color: #FBFBFB !important;

    border: 1px solid #1E40AF !important;
}
</style>

""", unsafe_allow_html=True) 

# ==========================================
# 🔌 ĐỌC/GHI DỮ LIỆU TỪ FILE JSON NGOÀI
# ==========================================
@st.cache_data
def load_questions_from_json():
    file_name = "question_bank.json"
    if os.path.exists(file_name):
        with open(file_name, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        return [{
            "id": "ERR", "question": "Error: 'question_bank.json' file not found!", 
            "options": ["N/A"], "correct": "N/A", "explanation": "", "source": "", "ai_engine": ""
        }]

@st.cache_data
def load_quiz_history():
    file_name = "quiz_history.json"
    if os.path.exists(file_name):
        with open(file_name, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

@st.cache_data
def save_quiz_history(score_str, percentage, time_taken_str, exam_details):
    file_name = "quiz_history.json"
    history = load_quiz_history()
    new_record = {
        "exam_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "Date/Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Score": score_str,
        "Percentage (%)": percentage,
        "Duration": time_taken_str,
        "details": exam_details  
    }
    history.append(new_record)
    with open(file_name, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=4)

@st.cache_data
def save_quiz_history_raw(updated_list):
    """Hàm ghi đè danh sách lịch sử mới sau khi đã xóa dòng vào file JSON"""
    import json
    # Thay 'quiz_history.json' bằng đúng tên file lưu lịch sử thực tế trong code của bạn
    with open("quiz_history.json", "w", encoding="utf-8") as f:
        json.dump(updated_list, f, ensure_ascii=False, indent=4)

# 💡 ĐÂY LÀ HÀM BẠN ĐANG BỊ THIẾU - HÃY THÊM NÓ VÀO ĐÂY:
@st.cache_data
def load_knowledge_from_json():
    file_name = "knowledge_hub.json"
    if os.path.exists(file_name):
        try:
            with open(file_name, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

@st.cache_data
def load_general_learning_data():
    file_path = "general_learning.json"
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            st.error(f"❌ Lỗi đọc file JSON: {str(e)}")
            return {}
    else:
        st.error("⚠️ Không tìm thấy file general_learning.json!")
        return {}


#Load tiếp các file dữ liệu json khác
def load_glossary_data():
    file_path = "Glossary.json"
    if os.path.exists(file_path):
        try:
            # Kiểm tra nếu file trống rỗng
            if os.path.getsize(file_path) == 0:
                return []
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("glossary", [])
        except Exception:
            return []
    return []
    


def render_agile_manifesto(manifesto_data: dict):
    """Render bảng Agile Manifesto 4 Values dạng HTML table."""

    st.info(f"💬 {manifesto_data.get('description', '')}")

    rows_html = ""
    for val in manifesto_data.get("values", []):
        # Đẩy sát các thẻ HTML ra lề trái để tránh bị Markdown hiểu là Code Block
        rows_html += f"""<tr style="border-bottom: 0.5px solid #E0E0E0;">
    <td style="padding:14px 12px; font-weight:600; color:#1565C0; font-size:1em; vertical-align:top; width:28%;">
        {val.get('left_side', '')}
    </td>
    <td style="padding:14px 6px; text-align:center; vertical-align:top; width:8%;">
        <span style="background:#F0F0F0; color:#888; font-size:0.72em; font-weight:bold; padding:3px 8px; border-radius:99px; text-transform:uppercase; letter-spacing:.05em;">
            over
        </span>
    </td>
    <td style="padding:14px 12px; color:#9E9E9E; font-size:1em; text-decoration-color:#ccc; vertical-align:top; width:24%;">
        {val.get('right_side', '')}
    </td>
    <td style="padding:14px 12px; font-size:0.88em; color:#555; line-height:1.6; vertical-align:top; border-left:1px solid #eee; width:40%;">
        {val.get('meaning', '')}
    </td>
</tr>"""

    # Tương tự với thẻ table
    table_html = f"""<table style="width:100%; border-collapse:collapse; margin-top:8px; border:1px solid #E0E0E0; border-radius:8px; overflow:hidden;">
    <thead>
        <tr style="border-bottom:1.5px solid #E0E0E0; background:#F8FAFF;">
            <th style="text-align:left; padding:10px 12px; font-size:0.78em; color:#1565C0; text-transform:uppercase;">
                ✅ More value
            </th>
            <th></th>
            <th style="text-align:left; padding:10px 12px; font-size:0.78em; color:#9E9E9E; text-transform:uppercase;">
                Over
            </th>
            <th style="text-align:left; padding:10px 12px; font-size:0.78em; color:#555; text-transform:uppercase;">
                Why it matters
            </th>
        </tr>
    </thead>
    <tbody>
        {rows_html}
    </tbody>
</table>"""

    st.markdown(table_html, unsafe_allow_html=True)

    if "critical_nuance" in manifesto_data:
        st.warning(f"⚠️ **Exam note:** {manifesto_data['critical_nuance']}")

# Nạp ngân hàng câu hỏi gốc
questions_bank = load_questions_from_json()
# ==========================================
# 📑 KHỞI TẠO CÁC BIẾN BỘ NHỚ (SESSION STATE)
# ==========================================
if "bank_current_idx" not in st.session_state:
    st.session_state.bank_current_idx = 0
if "bank_scores" not in st.session_state:
    st.session_state.bank_scores = {}
if "bank_finished" not in st.session_state:
    st.session_state.bank_finished = False

if "test_current_idx" not in st.session_state:
    st.session_state.test_current_idx = 0
if "test_mode" not in st.session_state:
    st.session_state.test_mode = False
if "test_questions" not in st.session_state:
    st.session_state.test_questions = []
if "test_scores" not in st.session_state:
    st.session_state.test_scores = {}
if "test_user_answers" not in st.session_state:
    st.session_state.test_user_answers = {}  
if "test_start_time" not in st.session_state:
    st.session_state.test_start_time = 0.0
if "test_total_seconds" not in st.session_state:
    st.session_state.test_total_seconds = 0

if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {"role": "assistant", "content": "👋 Hello! I am your specialized PMP & CAPM AI Tutor. I will answer your queries strictly in English to mimic the real exam environment. Configure your favorite AI provider on the left sidebar to start!"}
    ]


# ==========================================================
# 🧭 PHẦN 1: THANH ĐIỀU HƯỚNG & CẤU HÌNH API MULTI-LLM (PURE SIDEBAR)
# ==========================================================
st.sidebar.title("🎯 PMP/CAPM Learning Hub")

# 1. Khởi tạo thanh chọn Menu điều hướng chính
menu_choice = st.sidebar.radio(
    "Choose a feature:",
    ["🏠 Homepage", "📚 Knowledge Hub", "📝 Question Bank", "⏱️ Exam Simulator", "📊 Performance Dashboard", "🤖 AI Tutor Chat"]
)

st.sidebar.markdown("---")
st.sidebar.subheader("🔑 Live AI Engine Settings")
api_provider = st.sidebar.selectbox("AI Provider:", ["Google Gemini", "OpenAI", "Anthropic Claude"])
# 1. Lấy dữ liệu từ ô nhập của người dùng
user_api_key = st.sidebar.text_input(
    "Enter your API Key:", 
    type="password", 
    help="Key chỉ lưu tạm trong RAM phiên làm việc của trình duyệt."
)
# 2. KHAI BÁO VÀ ĐỊNH NGHĨA BIẾN active_api_key NGAY LẬP TỨC (Viết thường toàn bộ)
active_api_key = user_api_key.strip() 
using_fallback = False

# 3. Logic xử lý Fallback tự động bốc key hệ thống nếu người dùng để trống
if api_provider == "Google Gemini" and not active_api_key:
    if "GEMINI_API_KEY" in st.secrets:
        active_api_key = st.secrets["GEMINI_API_KEY"]  # Gán key hệ thống vào biến active_api_key
        using_fallback = True

# 4. Hiển thị thông báo trạng thái trên Sidebar
if using_fallback:
    st.sidebar.info("💡If you have API Key, please input it. Otherwise, auto select system's Gemini Free Tier. No API key required! ")
elif active_api_key:
    st.sidebar.success(f"✅ Personal {api_provider} Key loaded.")
else:
    st.sidebar.warning(f"⚠️ Please enter your {api_provider} API Key to chat.")

# 2. Các bộ điều hướng phụ (Navigators) hiển thị động trên Sidebar tùy theo trang chọn
if menu_choice == "📝 Question Bank" and not st.session_state.bank_finished:
    st.sidebar.markdown("---")
    st.sidebar.subheader("🗂️ Bank Navigator")
    
    # --- ĐOẠN CSS ĐỂ ĐỔI MÀU NỀN VÀ TỰ ĐỘNG CO GIÃN THEO SIDEBAR ---

    st.sidebar.markdown("""
            <style>
            /* 1. Nhắm thẳng vào thẻ chứa chữ/số bên trong button để hạ size xuống 7px */
            div[data-testid="stSidebar"] button p, 
            div[data-testid="stSidebar"] button span,
            div[data-testid="stSidebar"] button {
                font-size: 5px !important;
                line-height: 1 !important;
            }
            
            /* 2. Thu nhỏ độ cao (padding) của ô nút để cân đối với chữ 7px, tránh nút quá to chữ quá nhỏ */
            div[data-testid="stSidebar"] button {
                padding: 1px 1px !important;
                min-height: 18px !important; /* Hạ chiều cao tối thiểu của nút xuống để vừa vặn */
                max-height: 22px !important;
                margin: 0px !important;
                border-radius: 3px !important;
                width: 100% !important;
            }
            
            /* 3. Giữ khoảng cách giữa các ô thật khít để cố định 6 cột mượt mà */
            div[data-testid="stSidebar"] div[data-testid="stHorizontalBlock"] {
                gap: 3px !important;
                margin-bottom: 3px !important;
            }
            </style>
        """, unsafe_allow_html=True)
            
    # Cố định đúng 6 cột trên một hàng theo yêu cầu của bạn
    NUM_COLS = 5 
    
    # Chia danh sách câu hỏi thành từng nhóm nhỏ 6 câu
    for i in range(0, len(questions_bank), NUM_COLS):
        cols = st.sidebar.columns(NUM_COLS)
        
        for j in range(NUM_COLS):
            idx = i + j
            if idx < len(questions_bank):
                q = questions_bank[idx]
                
                # Xác định trạng thái câu hỏi để hiển thị trong tooltip (help)
                if q['id'] in st.session_state.bank_scores:
                    status_icon = "✅" if st.session_state.bank_scores[q['id']] else "❌"
                else:
                    status_icon = "⏳"
                
                # Kiểm tra xem ô này có phải là câu hỏi hiện tại không
                is_current = (idx == st.session_state.bank_current_idx)
                
                # Label bây giờ hoàn toàn là số thuần túy, không bị dính ký tự [ ]
                button_label = f"{idx+1}"
                
                # Hiển thị nút bấm
                with cols[j]:
                    # Sử dụng st.button thông thường, nếu là câu hiện tại (is_current=True), 
                    # ta dùng loại nút `type="primary"` của Streamlit để nó tự động đổi thành màu xanh đậm đặc trưng.
                    btn_type = "primary" if is_current else "secondary"
                    
                    if st.button(
                        button_label, 
                        key=f"btn_nav_{idx}", 
                        help=f"Question {idx+1} ({status_icon})", 
                        use_container_width=True,
                        type=btn_type
                    ):
                        if st.session_state.bank_current_idx != idx:
                            st.session_state.bank_current_idx = idx
                            st.rerun()
                    
#------Update sidebar for Exam simulator-----
elif menu_choice == "⏱️ Exam Simulator" and st.session_state.test_mode:
    st.sidebar.markdown("---")
    st.sidebar.subheader("🧩 Exam Navigator")
    test_labels = [f"Question {i+1} {'✅' if q['id'] in st.session_state.test_user_answers and st.session_state.test_scores.get(q['id']) else '❌' if q['id'] in st.session_state.test_user_answers else '⏳'}" for i, q in enumerate(st.session_state.test_questions)]
    chosen_test_idx = st.sidebar.radio("Jump to exam question:", options=range(len(st.session_state.test_questions)), format_func=lambda x: test_labels[x], index=st.session_state.test_current_idx)
    if chosen_test_idx != st.session_state.test_current_idx:
        st.session_state.test_current_idx = chosen_test_idx
        st.rerun()

# 3. Footer của Sidebar
with st.sidebar:
    st.markdown("---")
st.sidebar.caption("Version 7.3 | Multi-LLM (Gemini / OpenAI / Claude)")

# ==========================================================
# 📋 CẤU HÌNH TỪ VIẾT TẮT CHUYÊN NGÀNH CẦN BẢO VỆ VIẾT HOA
# ==========================================================
KEEP_UPPER = [
    "BA", "PM", "PO", "SME", "EEFs", "OPAs", "RTM", "QA", "IT", "SWOT", "MoSCoW", 
    "WBS", "UAT", "KPI", "KPIS", "CRM", "ROI", "NPV", "SLA", "SLAS", "SAAS", 
    "PERT", "EVM", "PV", "EV", "AC", "BAC", "EAC", "ETC", "VAC", "CCB", "HR", "UX","WSJF","PMO","PMI", "RACI", "RASIC", "RFQ","RFP","SOW","OSCAR","ADKAR","Drexler/Sibbet","Tuckman","Theory Y","McGregor", "XP","Scrum","Agile"
]

def format_text(text):
    """Xử lý văn bản: Viết hoa chữ cái đầu tiên của dòng, giữ nguyên từ khóa chuyên ngành."""
    if not text or not isinstance(text, str):
        return text
    words = text.split()
    if not words:
        return text
    
    formatted_words = []
    for i, word in enumerate(words):
        # Loại bỏ các dấu câu bọc quanh từ để kiểm tra trong danh sách viết tắt
        clean_word = word.strip(".,;:!?()\"'`[]{}*-")
        if clean_word.upper() in KEEP_UPPER:
            upper_clean = clean_word.upper()
            # Xử lý trường hợp đặc biệt viết thường xen kẽ (ví dụ: SaaS)
            if upper_clean == "SAAS":
                upper_clean = "SaaS"
            formatted_word = word.replace(clean_word, upper_clean)
            formatted_words.append(formatted_word)
        elif i == 0:
            # Viết hoa chữ cái đầu tiên khả dụng trong từ đầu tiên của dòng
            first_letter_idx = -1
            for idx, char in enumerate(word):
                if char.isalpha():
                    first_letter_idx = idx
                    break
            if first_letter_idx != -1:
                capitalized = word[:first_letter_idx] + word[first_letter_idx].upper() + word[first_letter_idx+1:]
                formatted_words.append(capitalized)
            else:
                formatted_words.append(word.capitalize())
        else:
            formatted_words.append(word)
            
    return " ".join(formatted_words)

def render_list_item(item, has_icon=False):
    """Hiển thị mục danh sách: Tự động bỏ chấm tròn đầu dòng nếu có icon."""
    if isinstance(item, str):
        formatted = format_text(item)
        if has_icon:
            st.markdown(f"{formatted}")
        else:
            st.markdown(f"• {formatted}")
    else:
        st.write(item)

def display_content_section(title, data_list, use_icons=False):
    """Hàm chuẩn hiển thị danh sách cho Inputs, Outputs, Tools & Techniques."""
    if data_list:
        st.markdown(f"**{title}**")
        for item in data_list:
            render_list_item(item, has_icon=use_icons)

# ==========================================================
# 🛡️ HÀM TRỢ GIÚP KẾT XUẤT DỮ LIỆU ĐỘNG (SMART DETAIL RENDERER)
# ==========================================================
# ==========================================================
# 🛡️ HÀM TRỢ GIÚP KẾT XUẤT DỮ LIỆU ĐỘNG (TỪ OLDCODE)
# ==========================================================
def render_nested_data(val, indent_level=1):
    """Hàm đệ quy thông minh giúp bóc tách mọi kiểu list/dict lồng nhau ở bất kỳ cấp độ nào, tránh in thô."""
    indent = "&nbsp;&nbsp;&nbsp;&nbsp;" * indent_level
    if isinstance(val, dict):
        if any(k in val for k in ["stated", "real_need", "ba_response"]):
            item_lines = []
            if "stated" in val: item_lines.append(f"🗣️ **Stated**: {format_text(val['stated'])}")
            if "real_need" in val: item_lines.append(f"🎯 **Real Need**: {format_text(val['real_need'])}")
            if "ba_response" in val: item_lines.append(f"🧠 **BA Response**: {format_text(val['ba_response'])}")
            for line in item_lines: st.markdown(f"{indent}{line}")
            return
            
        icon_map = {
            "stated": "🗣️ Stated", "real_need": "🎯 Real Need", "ba_response": "🧠 BA Response",
            "left": "👈 Left", "right": "👉 Right", "step": "👟 Step",
            "definition": "📖 Definition", "description": "📝 Description",
            "purpose": "🎯 Purpose", "focus": "🎯 Focus", "area": "🗂️ Area",
            "creator": "👤 Creator", "PM role": "👔 PM Role", "pm_application": "📋 PM Application",
            "symptom": "⚠️ Symptom", "type": "🏷️ Type", "quadrant": "📊 Quadrant",
            "strategy": "🎯 Strategy", "engagement": "🤝 Engagement", "example": "💡 Example",
            "examples": "💡 Examples", "attitude": "🎭 Attitude", "technique": "🛠️ Technique",
            "key_output": "📤 Key Output", "group": "🔄 Group","prevention":"❗Prevention","bad_example": "❌Bad Example","good_example":"✅Good Example"
        }
        
        for k, v in val.items():
            label = icon_map.get(k, k.replace('_', ' '))
            bullet = "" if k in icon_map else "• "
            if isinstance(v, (dict, list)):
                st.markdown(f"{indent}{bullet}**{format_text(label)}**:")
                render_nested_data(v, indent_level + 1)
            else:
                st.markdown(f"{indent}{bullet}**{format_text(label)}**: {format_text(str(v)) if isinstance(v, str) else v}")
                
    elif isinstance(val, list):
        for elem in val:
            if isinstance(elem, (dict, list)):
                render_nested_data(elem, indent_level)
            else:
                st.markdown(f"{indent}• {format_text(str(elem)) if isinstance(elem, str) else elem}")
    else:
        st.markdown(f"{indent}{format_text(str(val)) if isinstance(val, str) else val}")


def render_dict_item(item):
    """Tự động phân tích và format đẹp mắt mọi kiểu phần tử dictionary lồng nhau trong mảng."""
    if not isinstance(item, dict):
        render_list_item(str(item), has_icon=False)
        return

    icon_map = { # ... (Giữ nguyên icon map như trên)
         "stated": "🗣️ Stated", "real_need": "🎯 Real Need", "ba_response": "💬 BA Response", "step": "👟 Step",
            "definition": "📖 Definition", "description": "📝 Description",
            "purpose": "🎯 Purpose", "focus": "🎯 Focus", "area": "🗂️ Area",
            "creator": "👤 Creator", "PM role": "👔 PM Role", "pm_application": "📋 PM Application",
            "symptom": "⚠️ Symptom", "type": "🏷️ Type", "quadrant": "📊 Quadrant",
            "strategy": "🎯 Strategy", "engagement": "🤝 Engagement", "example": "💡 Example",
            "examples": "💡 Examples", "attitude": "🎭 Attitude", "technique": "🛠️ Technique",
            "key_output": "📤 Key Output", "group": "🔄 Group","prevention":"❗Prevention","bad_example": "❌Bad Example","good_example":"✅Good Example"
    }
    
    main_key = next((k for k in ["name", "section", "title", "step", "type", "attitude", "dimension", "area"] if k in item), None)
    
    if main_key:
        title_val = item[main_key]
        st.markdown(f"**• {format_text(str(title_val))}**")
        indent = "&nbsp;&nbsp;&nbsp;&nbsp;"
        for k, v in item.items():
            if k == main_key: continue
            has_icon = k in icon_map
            label = icon_map.get(k, k.replace('_', ' '))
            bullet = "" if has_icon else "- "
            
            if isinstance(v, (dict, list)):
                st.markdown(f"{indent}{bullet}**{format_text(label)}**:")
                render_nested_data(v, indent_level=2)
            else:
                st.markdown(f"{indent}{bullet}**{format_text(label)}**: {format_text(str(v)) if isinstance(v, str) else v}")
        return

    for k, v in item.items():
        has_icon = k in icon_map
        label = icon_map.get(k, k.replace('_', ' '))
        bullet = "" if has_icon else "• "
        if isinstance(v, (dict, list)):
            st.markdown(f"{bullet}**{format_text(label)}**:")
            render_nested_data(v, indent_level=1)
        else:
            st.markdown(f"{bullet}**{format_text(label)}**: {format_text(str(v)) if isinstance(v, str) else v}")


def render_sub_data(sub_data):
    """Hàm gốc mạnh mẽ từ oldcode.json để phân tích chi tiết từng block dữ liệu"""
    if isinstance(sub_data, dict):
        # 1. Định nghĩa chính
        for def_key in ["definition", "description"]:
            if def_key in sub_data:
                st.markdown(f"*{format_text(sub_data[def_key])}*")

        # 2. Đặc trưng (Characteristics)
        if "characteristics" in sub_data:
            st.markdown("**Characteristics:**")
            chars = sub_data["characteristics"]
            if isinstance(chars, list):
                for item in chars: render_dict_item(item)
            elif isinstance(chars, dict):
                for k, v in chars.items():
                    if isinstance(v, list):
                        st.markdown(f"• **{format_text(k.replace('_', ' '))}**:")
                        for li in v: st.markdown(f"  - {format_text(str(li))}")
                    else:
                        st.markdown(f"• **{format_text(k.replace('_', ' '))}**: {format_text(str(v)) if isinstance(v, str) else v}")
            elif isinstance(chars, str):
                for line in chars.replace("\r\n", "\n").split("\n"):
                    if line.strip(): st.markdown(f"• {format_text(line.strip())}")

        # 3. Hỗ trợ đặc thù Agile (Iterative & Incremental Characteristics)
        for spec_char_key in ["iterative_characteristics", "incremental_characteristics"]:
            if spec_char_key in sub_data:
                title_clean = spec_char_key.replace("_", " ")
                st.markdown(f"**{format_text(title_clean)}:**")
                spec_val = sub_data[spec_char_key]
                if isinstance(spec_val, list):
                    for item in spec_val:
                        render_dict_item(item)
                elif isinstance(spec_val, str):
                    for line in spec_val.replace("\r\n", "\n").split("\n"):
                        if line.strip():
                            st.markdown(f"• {format_text(line.strip())}")

        # 4. Các danh sách tiêu chuẩn khác (phases, impact, risks_associated, conditions, sections, rules)
        for list_key in ["phases", "impact", "risks_associated", "conditions", "sections", "rules"]:
            if list_key in sub_data:
                title_clean = list_key.replace("_", " ")
                st.markdown(f"**{format_text(title_clean)}:**")
                list_val = sub_data[list_key]
                if isinstance(list_val, list):
                    for item in list_val:
                        render_dict_item(item)
                elif isinstance(list_val, str):
                    st.markdown(f"• {format_text(list_val)}")

        # 5. CÁC LOẠI VÍ DỤ CHUYÊN SÂU
        for ex_key in ["internal_examples", "external_examples", "examples", "example", "iterative_examples", "incremental_examples"]:
            if ex_key in sub_data:
                title_clean = ex_key.replace("_", " ")
                st.markdown(f"**{format_text(title_clean)}:**")
                ex_val = sub_data[ex_key]
                if isinstance(ex_val, list):
                    for item in ex_val:
                        render_dict_item(item)
                elif isinstance(ex_val, dict):
                    for group_name, group_list in ex_val.items():
                        st.markdown(f"  * **{format_text(group_name.replace('_', ' '))}:**")
                        if isinstance(group_list, list):
                            for item in group_list:
                                st.markdown(f"    • {format_text(str(item))}")
                        else:
                            st.markdown(f"    • {format_text(str(group_list))}")
                elif isinstance(ex_val, str):
                    st.markdown(f"• {format_text(ex_val)}")

        # 6. Phù hợp nhất cho (Best For)
        if "best_for" in sub_data:
            st.success(f"🎯 **Best for:** {format_text(sub_data['best_for'])}")

        # 7. Fallback thông minh cho các Custom Key khác
        processed_keys = [
            "definition", "description", "characteristics", "phases", "impact", 
            "risks_associated", "internal_examples", "external_examples", 
            "example", "examples", "tools", "iterative_characteristics", 
            "incremental_characteristics", "conditions", "sections", "best_for", "rules"
        ]
        other_keys = [k for k in sub_data.keys() if k not in processed_keys]
        if other_keys:
            st.write("")
            for k in other_keys:
                k_clean = k.replace("_", " ")
                val = sub_data[k]
                if isinstance(val, (dict, list)):
                    st.markdown(f"**{format_text(k_clean)}**:")
                    render_nested_data(val, indent_level=1)
                else:
                    st.markdown(f"**{format_text(k_clean)}**: {format_text(str(val)) if isinstance(val, str) else val}")
                    
    elif isinstance(sub_data, list):
        st.write("")
        for item in sub_data:
            render_dict_item(item)
    elif isinstance(sub_data, str):
        st.write(format_text(sub_data))

# ==========================================================
# 🖥️ PHẦN 1.2: ĐIỀU HƯỚNG HIỂN THỊ NỘI DUNG CHÍNH (MAIN BODY MAIN LOOP)
# --- TRANG 1: COVERS PAGE (ĐÃ NÂNG CẤP LÊN GIAO DIỆN THẺ CARD ĐỒNG BỘ) ---
if menu_choice == "🏠 Homepage":
    # Tiêu đề lớn trung tâm
    st.title("🚀 Project Management Knowledge Hub")
    st.markdown("##### *A self-built website to support you on achieving your PMP® and CAPM® goals*")
    st.markdown("---")
    
    # Đoạn giới thiệu tổng quan
    st.markdown("""
    Welcome to the **PMP/CAPM Learning Hub**! This system is designed to provide an optimized learning experience, offering a structured approach to studying project management concepts, visual learning tools, and integrated AI assistance for instant clarification of doubts.
    
    👉 **Instructions:** Please select the desired features from the **left sidebar (Sidebar)** to begin your learning journey✒️.
    """)
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("💡 Discover System Features")
    
    # Thiết kế bố cục các tính năng dạng thẻ lồng trong 2 Cột
    col1, col2 = st.columns(2, gap="large")
    
    with col1:
        # Card 1: Knowledge Hub
        st.markdown("""
        <div class="task-card">
            <h3 style="margin-top: 0; margin-bottom: 10px;">📚 Knowledge Hub</h3>
            <p style="margin-bottom: 0;">Systematize all the <b>Tasks</b>, <b>Domains (People, Process, Business Environment)</b> according to the latest PMI syllabus. Helps you master the core theories and exam tips.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Card 2: Question Bank
        st.markdown("""
        <div class="task-card">
            <h3 style="margin-top: 0; margin-bottom: 10px;">📝 Question Bank</h3>
            <p style="margin-bottom: 0;">A rich repository of multiple-choice questions, categorized by topic. You can practice daily and view detailed explanations for each answer immediately.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Card 3: AI Tutor Chat
        st.markdown("""
        <div class="task-card">
            <h3 style="margin-top: 0; margin-bottom: 10px;">🤖 AI Tutor Chat</h3>
            <p style="margin-bottom: 0;">Your dedicated PMP expert AI assistant is available 24/7 to answer questions, analyze complex project management scenarios, and resolve any doubts you may have.</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        # Card 4: Exam Simulator
        st.markdown("""
        <div class="task-card">
            <h3 style="margin-top: 0; margin-bottom: 10px;">⏱️ Exam Simulator</h3>
            <p style="margin-bottom: 0;">Experience the real exam environment with full-length Mock Tests and time pressure. Helps you practice time management and build exam confidence.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Card 5: Performance Dashboard
        st.markdown("""
        <div class="task-card">
            <h3 style="margin-top: 0; margin-bottom: 10px;">📊 Performance Dashboard</h3>
            <p style="margin-bottom: 0;">Visualize your learning progress. Track scores across practice tests and analyze weak areas to create an effective improvement plan.</p>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("---")
    st.caption("Wishing you a wonderful study journey and success in achieving your certification goals! 🎯")

# ==========================================================
# 📚 PHẦN 2: KNOWLEDGE HUB (TABBED SYSTEM - FIXED UI)
# ==========================================================
if menu_choice == "📚 Knowledge Hub":
    st.title("📚 Professional Certification Knowledge Hub")

    # 1. Nạp dữ liệu từ các file JSON
    eco_data = load_knowledge_from_json()          # PMP/CAPM
    general_data = load_general_learning_data()    # General Learning
    glossary_data = load_glossary_data()          # Bảng thuật ngữ

    # 2. Tạo 3 thanh Tab ngang ở trên cùng đúng theo thiết kế của bạn
    tab_pmp, tab_capm, tab_general = st.tabs(["🏆 PMP®", "🎓 CAPM® Core", "📖 General Learning"])

    # Định nghĩa sẵn bảng màu Pastel cho thẻ Task (Dùng chung cho PMP/CAPM)
    approach_colors = {
        "PREDICTIVE": {"bg": "#E3F2FD", "text": "#0D47A1"},
        "AGILE": {"bg": "#E8F5E9", "text": "#41B67C"},
        "BOTH": {"bg": "#F3E5F5", "text": "#4A148C"}
    }

    # ==========================================================
    # KHỐI 1: TỰ ĐỘNG XỬ LÝ CHO TAB PMP (ĐÃ NÂNG CẤP EXPANDER)
    # ==========================================================
    with tab_pmp:
        pmp_domains = ["People", "Process", "Business Environment"]
        col_menu_pmp, col_content_pmp = st.columns([1, 3])
        
        with col_menu_pmp:
            selected_domain = st.radio("Select Domain:", pmp_domains, key="pmp_radio")

        with col_content_pmp:
            st.subheader(f"📖 {selected_domain}")
            tasks = [t for t in eco_data if t.get("domain") == selected_domain]
            
            if not tasks:
                st.info("No tasks found for this domain.")
            else:
                for t_data in tasks:
                    raw_approach = str(t_data.get('approach', '')).upper().strip()
                    color_cfg = approach_colors.get(raw_approach, approach_colors["BOTH"])
                    approach_badge_html = f'<span style="background-color: {color_cfg["bg"]}; color: {color_cfg["text"]}; padding: 2px 10px; border-radius: 6px; font-weight: bold; font-size: 0.85em; display: inline-block; border: 1px solid {color_cfg["text"]}20;">{raw_approach}</span>'
                    
                    # Dùng Expander để bọc nội dung, chỉ hiện tiêu đề Task
                    task_title = f"Task {t_data.get('task_number', '')}: {t_data.get('task', 'Untitled')}"

                    with st.expander(f"📌 {task_title}", expanded=False):
                        st.markdown(f"""
                            <div class="task-card">
                                <div style="line-height: 1.8;font-size:0.9em;">
                                    <b>Approach:</b> {approach_badge_html}<br>
                                    <div style="margin-top: 6px;"><b>Summary:</b> {t_data.get('summary', 'N/A')}</div>
                                    <b>Key Concepts:</b> {', '.join(t_data.get('key_concepts', []))}
                                </div>
                                <div style="background-color: #F5F5F5; color: #555; padding: 10px; border-radius: 8px; margin-top: 15px; font-size:0.9em;">
                                    💡 <b>Exam Tip:</b> {t_data.get('exam_tips', 'N/A')}
                                </div>
                            </div>
                        """, unsafe_allow_html=True)

    # ==========================================================
    # KHỐI 2: TỰ ĐỘNG XỬ LÝ CHO TAB CAPM (ĐÃ NÂNG CẤP EXPANDER)
    # ==========================================================
    with tab_capm:
        capm_domains = [
            "Project Management Fundamentals and Core Concepts", 
            "Predictive, Plan-Based Methodologies", 
            "Agile Frameworks/Methodologies", 
            "Business Analysis Frameworks"
        ]
        col_menu_capm, col_content_capm = st.columns([1, 3])
        
        with col_menu_capm:
            selected_domain = st.radio("Select Domain:", capm_domains, key="capm_radio")

        with col_content_capm:
            st.subheader(f"📖 {selected_domain}")
            tasks = [t for t in eco_data if t.get("domain") == selected_domain]
            
            if not tasks:
                st.info("No tasks found for this domain.")
            else:
                for t_data in tasks:
                    raw_approach = str(t_data.get('approach', '')).upper().strip()
                    color_cfg = approach_colors.get(raw_approach, approach_colors["BOTH"])
                    approach_badge_html = f'<span style="background-color: {color_cfg["bg"]}; color: {color_cfg["text"]}; padding: 2px 10px; border-radius: 6px; font-weight: bold; font-size: 0.85em; display: inline-block; border: 1px solid {color_cfg["text"]}20;">{raw_approach}</span>'
                    
                    # Dùng Expander để bọc nội dung, chỉ hiện tiêu đề Task
                    task_title = f"Task {t_data.get('task_number', '')}: {t_data.get('task', 'Untitled')}"
                    with st.expander(f"📌 {task_title}", expanded=False):
                        st.markdown(f"""
                            <div class="task-card">
                                <div style="line-height: 1.8;font-size:0.9em;">
                                    <b>Approach:</b> {approach_badge_html}<br>
                                    <div style="margin-top: 6px;"><b>Summary:</b> {t_data.get('summary', 'N/A')}</div>
                                    <b>Key Concepts:</b> {', '.join(t_data.get('key_concepts', []))}
                                </div>
                                <div style="background-color: #F5F5F5; color: #555; padding: 10px; border-radius: 8px; margin-top: 15px; font-size:0.9em;">
                                    💡 <b>Exam Tip:</b> {t_data.get('exam_tips', 'N/A')}
                                </div>
                            </div>
                        """, unsafe_allow_html=True)

    # ==========================================================
    # KHỐI 3: TỰ ĐỘNG XỬ LÝ CHO TAB GENERAL LEARNING (GỒM GLOSSARY SEARCH)
    # ==========================================================
    
    
    with tab_general:

        # ✅ 1. DEFINE ORDER
        domain_order = {
            "Project Management Fundamentals and Core Concepts": 1,
            "Predictive, Plan-Based Methodologies": 2,
            "Agile Frameworks/Methodologies": 3,
            "Business Analysis Frameworks": 4,
            "General leadership and interpersonal skills": 5,
            "Reference & Books": 6
        }
        # ✅ 2. LOAD + EXTRACT DOMAIN (PHẢI NẰM TRONG TAB)
        general_domains = []

        if general_data and isinstance(general_data, list):
            for item in general_data:
                d = str(item.get("domain", "")).strip()
                if d and d not in general_domains:
                    general_domains.append(d)

        # ✅ 3. SORT (PHẢI NẰM TRONG TAB)
        general_domains = sorted(
            general_domains,
            key=lambda x: domain_order.get(x, 999)
        )
                
        # CHÈN THÊM GLOSSARY VÀO LÀM MỘT DOMAIN RIÊNG BIỆT DƯỚI BẢNG ĐIỀU HƯỚNG DỌC
        glossary_domain_title = "🔤 Glossary & Terminology"
        general_domains.append(glossary_domain_title)
            

        if not general_domains:
            st.info("💡 Chưa có danh mục kiến thức General Learning nào được tìm thấy.")
        else:
            # Layout sidebar giả lập bên trong Tab General Learning
            col_menu_gen, col_content_gen = st.columns([1, 3])
             
            with col_menu_gen:
                selected_domain_gen = st.radio("Select Domain:", general_domains, key="general_radio")
            
                # ✅ highlight (đặt NGAY SAU radio)
                if selected_domain_gen:
                    st.markdown(f"""
                    <div style="background-color:#C3E0F5;
                                padding:8px;
                                border-radius:6px;
                                margin-top:10px;">
                        ✅ <b>Selecting Domain:</b> {selected_domain_gen}
                    </div>
                    """, unsafe_allow_html=True)


            with col_content_gen:

                # ------------------------------------------------------
                # KỊCH BẢN 3.1: NẾU USER CHỌN DOMAIN GLOSSARY (XỬ LÝ DỮ LIỆU TỪ Glossary.json)
                # ------------------------------------------------------
                if selected_domain_gen == glossary_domain_title:
                    st.subheader("🔤 Project Management Glossary")
                    st.markdown("*Quickly search for  project management terms, acronyms, terminology and concepts aligned with PMI and Agile/Scrum standards*")
                    st.markdown("---")
                    
                    if not glossary_data:
                        st.warning("⚠️ Do not find Glossary.json file or the file format is invalid.")
                    else:
                        # Chia làm 2 cột: Cột 1 nhập từ khóa tìm kiếm, Cột 2 lọc theo Category (General, Agile, Cost, Schedule,...)
                        col_search, col_filter = st.columns([2, 1])
                        
                        with col_search:
                            search_query = st.text_input("🔍 Search term or definition:", placeholder="Type to search (e.g. WBS, Agile, AC, Baseline)...", key="glossary_main_search_bar")
                        
                        with col_filter:
                            # Tự động lấy danh sách Category xuất hiện trong Glossary để lọc
                            categories_list = sorted(list(set(str(item.get("category", "General")) for item in glossary_data if item.get("category"))))
                            selected_category = st.selectbox("🗂️ Filter by Category:", ["All Categories"] + categories_list, key="glossary_cat_selectbox")
                        
                        # LOGIC LỌC TÌM KIẾM ĐỘNG
                        filtered_glossary = glossary_data
                        
                        # 1. Lọc theo Category
                        if selected_category != "All Categories":
                            filtered_glossary = [item for item in filtered_glossary if str(item.get("category")) == selected_category]
                        
                        # 2. Lọc theo Từ khóa tìm kiếm (Không phân biệt hoa thường)
                        if search_query.strip():
                            q = search_query.lower().strip()
                            filtered_glossary = [
                                item for item in filtered_glossary
                                if q in str(item.get("term", "")).lower() or q in str(item.get("definition", "")).lower()
                            ]
                        
                        # Hiển thị số lượng kết quả
                        st.caption(f"Showing {len(filtered_glossary)} of {len(glossary_data)} terms found.")
                        st.write("")
                        
                        # Render danh sách kết quả (Giới hạn tối đa 80 thẻ đầu tiên để tránh làm lag trình duyệt khi tải quá nặng)
                        display_limit = 80
                        for idx, item in enumerate(filtered_glossary[:display_limit]):
                            term_name = item.get("term", "N/A")
                            term_def = item.get("definition", "No definition provided.")
                            term_cat = item.get("category", "General")
                            
                            # Tô đậm từ khóa tìm kiếm trong định nghĩa và thuật ngữ nếu có
                            st.markdown(f"""
                                <div class="task-card" style="margin-bottom: 12px; padding: 15px;">
                                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                                        <span style="font-weight: bold; font-size: 1.15em; color: #2799C7;">🏷️ {term_name}</span>
                                        <span style="background-color: #E0F2F1; color: #00796B; padding: 2px 8px; border-radius: 4px; font-size: 0.75em; font-weight: bold;">
                                            {term_cat.upper()}
                                        </span>
                                    </div>
                                    <div style="line-height: 1.6; font-size: 1.05em; opacity: 0.9;">
                                        {term_def}
                                    </div>
                                </div>
                            """, unsafe_allow_html=True)
                        
                        if len(filtered_glossary) > display_limit:
                            st.info(f"💡 Showing {display_limit} first answers. Please input more specific keywords to narrow down searching area!")


                # ------------------------------------------------------
                # KỊCH BẢN 3.2: NẾU USER CHỌN CÁC DOMAIN CÒN LẠI (GIẢM THIỂU CUỘN CHUỘT & FIXED CONFIGURATION TABS)
                # ------------------------------------------------------
                else:
                    domain_concepts = [c for c in general_data if str(c.get('domain')) == selected_domain_gen]
                    
                    if not domain_concepts:
                        st.info("No content found for this general learning domain.")
                    else:
                        concept_titles = [c.get("title", "Untitled Concept") for c in domain_concepts]
                        
                        selected_concept_title = st.selectbox(
                            "📚 Choose a Topic to Study:",
                            options=concept_titles,
                            key="concept_selector_dropdown"
                        )
                        
                        st.markdown("---")
                        
                        concept = next((c for c in domain_concepts if c.get("title") == selected_concept_title), domain_concepts[0])
                        
                
                        raw_approach = str(concept.get('approach', '')).upper().strip()
                        color_cfg = approach_colors.get(raw_approach, approach_colors["BOTH"])
                        approach_badge_html = f'<span style="background-color: {color_cfg["bg"]}; color: {color_cfg["text"]}; padding: 2px 10px; border-radius: 6px; font-weight: bold; font-size: 0.8em; display: inline-block; border: 1px solid {color_cfg["text"]}20;">{raw_approach}</span>'
                        
                        st.markdown(f"""
                            <div class="task-card" style="margin-bottom: 20px;">
                                <div style="font-weight: bold; font-size: 1.4em; color: #2799C7; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
                                    <span>📘 {format_text(concept.get('title', 'Untitled Concept'))}</span>
                                    {approach_badge_html}
                                </div>
                                <div style="font-size: 1.1em; line-height: 1.6; font-style: italic; opacity: 0.85;">
                                    {format_text(concept.get('summary', 'No summary available.'))}
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        if concept.get("key_concepts"):
                            with st.expander("📌 Key Concepts Summary", expanded=True):
                                for kc in concept.get("key_concepts", []):
                                    st.markdown(f"- {format_text(kc)}")

                        details = concept.get("details", {})
                        if details is None:
                            details = {}

                        tab_titles = [
                            "Project vs Program vs Portfolio",
                            "Strategic Dependencies (Project – Program – Portfolio)",
                            "Constraints, Assumptions, and Risks",
                            "Product, Product Life Cycle, and Project Life Cycle",
                            "Working with OPAs and EEFs",
                            "Project Development Approach",
                            "Leadership Styles in Project Management",
                            "Integration Management (Deep Dive)",
                            "Process Groups Overview",
                            "Knowledge Areas Overview",
                            "Agile Mindset — The Foundation of All Agile Approaches",
                            "Scrum Framework — Roles, Events, and Artifacts",
                            "Kanban — Visualizing Flow and Managing Work-in-Progress",
                            "Extreme Programming (XP) — Technical Excellence in Agile",
                            "Agile Planning — From Vision to Iteration",
                            "Agile Teams — Self-Organization, Cross-Functionality, and High Performance",
                            "Agile Metrics — Measuring Progress and Performance",
                            "Scaled Agile — Coordinating Multiple Agile Teams",
                            "Hybrid Approaches — Combining Predictive and Agile",
                            "Agile in the Organization — Adoption, Change, and Culture",
                            "Agile Requirements — User Stories, Epics, and the Product Backlog",
                            "Agile Quality — Building Quality In from the Start",
                            "Needs Assessment — Defining the Real Business Problem",
                            "Stakeholder Engagement in Business Analysis",
                            "Elicitation — Drawing Out Requirements from Stakeholders",
                            "Requirements Analysis — Modeling, Validating, and Prioritizing",
                            "Requirements Traceability — Tracking Requirements Through the Lifecycle",
                            "Solution Evaluation — Assessing Whether the Solution Delivers Value",
                            "Product Roadmap and Backlog in BA Context",
                            "Business Analysis — Overview, Role, and Value",
                            "Business Analysis Communication — Adapting to Different Audiences",
                            "BA Tools and Techniques Reference Guide",
                            "Team Development & Performance",
                            "Conflict Management & Negotiation"
                        ]
                        # So khớp thông minh không phân biệt hoa thường
                        use_tabs = any(concept.get("title", "").strip().lower() == t.strip().lower() for t in tab_titles)

                        # ------------------------------------------------------
                        # XỬ LÝ KHỐI 4.1: NẾU LÀ BÀI TOÁN MA TRẬN TIẾN TRÌNH (type == "matrix" hoặc có key matrix)
                        # ------------------------------------------------------
                        if concept.get("type") == "matrix" or "matrix" in concept or concept.get("id") == "PM-49-PROCESSES-MATRIX":
                            matrix_data = concept.get("matrix", {})
                            for group, areas in matrix_data.items():
                                with st.expander(f"🔹 {format_text(group.replace('_', ' '))}", expanded=True):
                                    html_code = """
                                    <style>
                                    .matrix-grid {
                                        display: flex;
                                        flex-wrap: wrap;
                                        gap: 12px;
                                        margin-top: 10px;
                                        width: 100%;
                                    }
                                    .matrix-card {
                                        flex: 1 1 200px;
                                        min-width: 160px;
                                        background-color: rgba(39, 153, 199, 0.05);
                                        border-left: 3px solid #2799C7;
                                        border-radius: 4px;
                                        padding: 10px;
                                    }
                                    .matrix-card-title {
                                        font-weight: bold;
                                        font-size: 0.9em;
                                        color: #1E3A8A;
                                        margin-bottom: 6px;
                                        border-bottom: 1px dashed rgba(30, 58, 138, 0.2);
                                        padding-bottom: 4px;
                                    }
                                    .matrix-process {
                                        font-size: 0.82em;
                                        line-height: 1.4;
                                        margin-bottom: 4px;
                                        color: #333333;
                                    }
                                    </style>
                                    <div class="matrix-grid">
                                    """
                                    for area, processes in areas.items():
                                        html_code += f'<div class="matrix-card"><div class="matrix-card-title">{format_text(area)}</div>'
                                        for p in processes:
                                            html_code += f'<div class="matrix-process">• {format_text(p)}</div>'
                                        html_code += '</div>'
                                    html_code += '</div>'
                                    st.markdown(html_code, unsafe_allow_html=True)

                        # ==========================================================
                        # KHỐI 4.2: TÍCH HỢP GIAO DIỆN MỚI CỦA BẠN (Tabs + Agile Table)
                        # ==========================================================
                        elif isinstance(details, dict) and details:
                            
                            # Tách riêng các key đặc biệt cần HTML tùy biến
                            SPECIAL_KEYS = {"agile_manifesto_four_values", "twelve_principles", "agile_vs_predictive_mindset"}
                            
                            if use_tabs:
                                st.markdown("---")
                                st.markdown("### 🔍 Detailed Breakdown & Comparisons")
                                tab_names = [format_text(k.replace('_', ' ')).upper() for k in details.keys()]
                                inner_tabs = st.tabs(tab_names)
                                
                                for idx, key in enumerate(details.keys()):
                                    with inner_tabs[idx]:
                                        sub_data = details[key]
                                        if key == "agile_manifesto_four_values":
                                            render_agile_manifesto(sub_data) # Bảng HTML từ code mới
                                        else:
                                            render_sub_data(sub_data) # Hàm đệ quy chống in thô từ code cũ
                            else:
                                st.markdown("---")
                                st.markdown("### 🔍 Detailed Breakdown & Comparisons")
                                
                                # Render trước các khối đặc biệt
                                if "agile_manifesto_four_values" in details:
                                    render_agile_manifesto(details["agile_manifesto_four_values"])
                                    
                                if "twelve_principles" in details:
                                    st.markdown("<br>", unsafe_allow_html=True)
                                    st.markdown("#### 📜 12 Agile Principles")
                                    p_data = details["twelve_principles"]
                                    st.caption(p_data.get("description", ""))
                                    for i, p in enumerate(p_data.get("principles", []), 1):
                                        st.markdown(f"**{i}.** {p}")

                                if "agile_vs_predictive_mindset" in details:
                                    st.markdown("<br>", unsafe_allow_html=True)
                                    st.markdown("#### 🔄 Predictive vs Agile Mindset")
                                    m_data = details["agile_vs_predictive_mindset"]
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        st.markdown("**🏗️ Predictive**")
                                        st.info(m_data.get("predictive_mindset", ""))
                                    with col2:
                                        st.markdown("**⚡ Agile**")
                                        st.success(m_data.get("agile_mindset", ""))
                                    st.markdown(f"💡 **Key Shift:** {m_data.get('key_shift', '')}")

                                # ── 2. Vòng lặp duyệt tự động qua các key còn lại (như SMART, types) ──
                                # Đã xử lý chuẩn lùi lề (indentation) để không bị lỗi nuốt dữ liệu
                                for sub_title, sub_data in details.items():
                                    if sub_title in SPECIAL_KEYS:
                                        continue

                                    # Tạo block tiêu đề xanh
                                    st.markdown(
                                        f"<div style='border-left:4px solid #2799C7; padding-left:15px;"
                                        f"margin-top:20px; margin-bottom:10px;'>"
                                        f"<span style='font-size:1.15em; font-weight:bold; color:#1E3A8A;'>"
                                        f"{format_text(sub_title.replace('_', ' ')).upper()}</span></div>",
                                        unsafe_allow_html=True
                                    )
                                    render_sub_data(sub_data) # Quét sâu mọi list/dict lồng nhau!
                                
                        # --- HỖ TRỢ HIỂN THỊ CÁC THUỘC TÍNH ROOT-LEVEL ---
                        root_characteristics = concept.get("characteristics")
                        if root_characteristics:
                            with st.expander("📋 Characteristics", expanded=False):
                                if isinstance(root_characteristics, list):
                                    for char in root_characteristics:
                                        render_list_item(char)
                                elif isinstance(root_characteristics, str):
                                    for line in root_characteristics.replace("\r\n", "\n").split("\n"):
                                        if line.strip(): render_list_item(line.strip())

                        root_when_to_use = concept.get("when_to_use") or concept.get("when to use")
                        if root_when_to_use:
                            with st.expander("🎯 When to Use & Apply", expanded=False):
                                if isinstance(root_when_to_use, list):
                                    for item in root_when_to_use:
                                        render_list_item(item)
                                elif isinstance(root_when_to_use, str):
                                    for line in root_when_to_use.replace("\r\n", "\n").split("\n"):
                                        if line.strip(): render_list_item(line.strip())
                                elif isinstance(root_when_to_use, dict):
                                    if "description" in root_when_to_use:
                                        st.markdown(f"*{format_text(root_when_to_use['description'])}*")
                                    if "conditions" in root_when_to_use and isinstance(root_when_to_use["conditions"], list):
                                        for cond in root_when_to_use["conditions"]:
                                            render_list_item(cond)

                        root_when_not_to_use = concept.get("when_not_to_use") or concept.get("when not to use")
                        if root_when_not_to_use:
                            with st.expander("⚠️ When NOT to Use", expanded=False):
                                if isinstance(root_when_not_to_use, list):
                                    for item in root_when_not_to_use:
                                        render_list_item(item)
                                elif isinstance(root_when_not_to_use, str):
                                    for line in root_when_not_to_use.replace("\r\n", "\n").split("\n"):
                                        if line.strip(): render_list_item(line.strip())
                                elif isinstance(root_when_not_to_use, dict):
                                    if "description" in root_when_not_to_use:
                                        st.markdown(f"*{format_text(root_when_not_to_use['description'])}*")
                                    if "conditions" in root_when_not_to_use and isinstance(root_when_not_to_use["conditions"], list):
                                        for cond in root_when_not_to_use["conditions"]:
                                            render_list_item(cond)

                        # 3.5. Real-World Examples & Applications
                        has_any_example = False
                        details_safe = concept.get("details", {})
                        if isinstance(details_safe, dict):
                            for sub_title, sub_data in details_safe.items():
                                if isinstance(sub_data, dict):
                                    for check_key in ["example", "examples", "internal_examples", "external_examples", "iterative_examples", "incremental_examples"]:
                                        if check_key in sub_data:
                                            has_any_example = True
                                            break
                                if has_any_example:
                                    break
                        if any(k in concept for k in ["example", "examples", "internal_examples", "external_examples"]):
                            has_any_example = True

                        if has_any_example:
                            if not use_tabs:
                                root_exs = concept.get("examples") or concept.get("example")
                                if not root_exs and isinstance(details_safe, dict):
                                    root_exs = details_safe.get("real_world_example") or details_safe.get("real world example")
                                
                                if root_exs:
                                    with st.expander("💡 Real-world Examples & Applications", expanded=False):
                                        st.markdown(f"<div style='border-left: 3px solid #FF9800; padding: 10px; border-radius: 4px;'>", unsafe_allow_html=True)
                                        if isinstance(root_exs, list):
                                            for ex in root_exs:
                                                render_list_item(ex)
                                        elif isinstance(root_exs, str):
                                            for line in root_exs.replace("\r\n", "\n").split("\n"):
                                                if line.strip(): render_list_item(line.strip())
                                        st.markdown("</div>", unsafe_allow_html=True)
                        
                        # 4. Core Values (PMI Code of Ethics)
                        core_values = concept.get("core_values")
                        if core_values and isinstance(core_values, list):
                            with st.expander("🛡️ PMI Core Values & Ethical Conduct Guidelines", expanded=False):
                                for val in core_values:
                                    st.markdown(f"**⭐ {format_text(val.get('name', 'Value'))}**: *{format_text(val.get('definition', ''))}*")
                                    col_v1, col_v2 = st.columns(2)
                                    with col_v1:
                                        st.markdown("**Expected Behaviors:**")
                                        for behavior in val.get("behaviors", []):
                                            st.markdown(f"✅ {format_text(behavior)}")
                                    with col_v2:
                                        st.markdown("**PM Application:**")
                                        for app in val.get("pm_application", []):
                                            st.markdown(f"📋 {format_text(app)}")
                                    st.markdown("---")

                        # 5. Ethical Scenarios
                        ethical_scenarios = concept.get("ethical_scenarios")
                        if ethical_scenarios and isinstance(ethical_scenarios, list):
                            with st.expander("💼 Real-world Ethical Scenarios & Solutions", expanded=False):
                                for idx, sc in enumerate(ethical_scenarios):
                                    st.markdown(f"""
                                    <div style="background-color: #FFF9C4; border-left: 4px solid #FBC02D; padding: 12px; border-radius: 6px; margin-bottom: 10px; color: #212121;">
                                        <b>Scenario {idx+1}:</b> {format_text(sc.get('scenario', ''))}<br>
                                        ⚠️ <b>Violation:</b> <span style="color: #D32F2F; font-weight: bold;">{format_text(sc.get('violation', ''))}</span><br>
                                        ✔️ <b>Correct Professional Action:</b> <span style="color: #388E3C; font-weight: bold;">{format_text(sc.get('correct_action', ''))}</span>
                                    </div>
                                    """, unsafe_allow_html=True)

                        # 6. Dependency Types
                        dep_types = concept.get("dependency_types")
                        if dep_types and isinstance(dep_types, list):
                            with st.expander("🔗 Dependency Types Explained", expanded=False):
                                dep_cols = st.columns(len(dep_types))
                                for idx, dep in enumerate(dep_types):
                                    with dep_cols[idx]:
                                        st.markdown(f"""
                                        <div style="padding: 10px; border-radius: 6px; border-top: 3px solid #607D8B; height: 100%;">
                                            <b>{format_text(dep.get('type', ''))}</b><br>
                                            <span style="font-size: 0.9em; opacity: 0.8;">{format_text(dep.get('description', ''))}</span>
                                        </div>
                                        """, unsafe_allow_html=True)

                        # 7. Inputs, Outputs, Methods & Tools (ITTOs)
                        if any(concept.get(key) for key in ["inputs", "outputs", "methods_tools"]):
                            with st.expander("📊 Inputs, Tools & Outputs (ITTOs)", expanded=False):
                                col_in, col_out, col_mt = st.columns(3)
                                with col_in:
                                    display_content_section("📥 Inputs:", concept.get("inputs", []), use_icons=False)
                                with col_out:
                                    display_content_section("📤 Outputs:", concept.get("outputs", []), use_icons=False)
                                with col_mt:
                                    display_content_section("🛠️ Methods & Tools:", concept.get("methods_tools", []), use_icons=False)

                        # 8. Mẹo phòng thi (Exam Tips)
                        if concept.get("exam_tips"):
                            st.markdown(f"""
                                <div style="background-color: #F5F5F5; color: #333; padding: 12px; border-radius: 8px; margin-top: 15px; font-size:0.95em; border-left: 5px solid #FF9800;">
                                    💡 <b>Exam Tip:</b> {format_text(concept.get('exam_tips', 'N/A'))}
                                </div>
                            """, unsafe_allow_html=True)

# ==========================================
# 📝 PHẦN 3: QUESTION BANK
# ==========================================
elif menu_choice == "📝 Question Bank":
    st.title("📝 Question Bank Practice")
    st.markdown("---")
    # 🌟 CSS GIỚI HẠN PHẠM VI: Chỉ phóng to chữ và giãn dòng đáp án tại vùng nội dung chính
    st.markdown("""
        <style>
            /* Nhắm trực tiếp vào phần văn bản của đáp án (Radio) ở màn hình chính */
            [data-testid="stMainBlockContainer"] div[data-testid="stRadio"] div[role="radiogroup"] label p {
                font-size: 1.15rem !important; /* Tăng kích cỡ chữ đáp án */
                line-height: 1.6 !important;    /* Giãn khoảng cách các dòng trong một đáp án dài */
            }
            
            /* Tạo khoảng cách dọc thoáng hơn giữa các câu lựa chọn A, B, C, D */
            [data-testid="stMainBlockContainer"] div[data-testid="stRadio"] div[role="radiogroup"] {
                gap: 12px !important;           
            }
        </style>
    """, unsafe_allow_html=True)
    
    if st.session_state.bank_finished:
        st.header("🏁 Practice Session Finished")
        total_q = len(questions_bank)
        correct_q = sum(1 for q_id in st.session_state.bank_scores if st.session_state.bank_scores[q_id] is True)
        pct = (correct_q / total_q) * 100
        col1, col2 = st.columns(2)
        with col1: st.metric("Correct", f"{correct_q} / {total_q}")
        with col2: st.metric("Score (%)", f"{pct:.2f}%")
        if st.button("🔄 Restart Practice"):
            st.session_state.bank_current_idx = 0
            st.session_state.bank_scores = {}
            st.session_state.bank_finished = False
            st.rerun()
    else:
        idx = st.session_state.bank_current_idx
        selected_q = questions_bank[idx]
        st.write(f"**Question {idx + 1} of {len(questions_bank)}**")
        st.subheader(selected_q["question"])
        
        ans = st.radio("Select your option:", selected_q["options"], key=f"bank_{selected_q['id']}")
        
        if st.button("Submit Answer", key=f"btn_bank_{selected_q['id']}"):
            if ans == selected_q["correct"]:
                st.success("🎉 CORRECT!")
                st.session_state.bank_scores[selected_q["id"]] = True
                
                # --- HIỂN THỊ MAPPING NGAY CẢ KHI ĐÚNG ---
                st.markdown(f"""
                <div style="background-color: #E8F5E9; padding: 12px; border-radius: 10px; border-left: 5px solid #4CAF50; margin-top: 10px;">
                    <p style="margin: 0; color: #2E7D32;">
                        ✅ <b>Keep it up!</b> This question belongs to:<br>
                        🎓 Certification: <code>{selected_q.get('certification', 'N/A')}</code><br>
                        📂 Domain: <code>{selected_q.get('domain', 'N/A')}</code>
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                with st.expander("🔍 View AI Explanation & Source"):
                    st.write(selected_q["explanation"])
                    st.caption(f"Source: {selected_q['source']} | AI: {selected_q['ai_engine']}")
            else:
                st.error("❌ INCORRECT! Please try again.")
                st.session_state.bank_scores[selected_q["id"]] = False
                
                # --- HIỂN THỊ MAPPING KHI SAI (Giữ nguyên hoặc dùng màu xanh dương) ---
                st.markdown(f"""
                <div style="background-color: #E3F2FD; padding: 12px; border-radius: 10px; border-left: 5px solid #1E88E5; margin-top: 10px;">
                    <p style="margin: 0; color: #333;">
                        📖 <b>Review this concept:</b><br>
                        🎓 Certification: <code>{selected_q.get('certification', 'N/A')}</code><br>
                        📂 Domain: <code>{selected_q.get('domain', 'N/A')}</code>
                    </p>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("---")
        c1, c2, c3 = st.columns([1, 1, 1])
        with c1:
            if st.button("⬅️ Previous") and idx > 0: st.session_state.bank_current_idx -= 1; st.rerun()
        with c2:
            if idx < len(questions_bank) - 1:
                if st.button("Next ➡️"): st.session_state.bank_current_idx += 1; st.rerun()
        with c3:
            if st.button("🏁 Finish Practice", type="primary"): st.session_state.bank_finished = True; st.rerun()

# ==========================================
# ⏱️ PHẦN 4: EXAM SIMULATOR
# ==========================================
elif menu_choice == "⏱️ Exam Simulator":
    st.markdown("""
        <style>
            /* Chỉ tìm các div stRadio nằm bên trong vùng Main Content */
            [data-testid="stMainBlockContainer"] div[data-testid="stRadio"] div[role="radiogroup"] label p {
                font-size: 1.15rem !important; /* Tăng cỡ chữ đáp án */
                line-height: 1.6 !important;    /* Giãn dòng văn bản */
            }
            
            [data-testid="stMainBlockContainer"] div[data-testid="stRadio"] div[role="radiogroup"] {
                gap: 12px !important;           /* Giãn khoảng cách dọc giữa câu A, B, C, D */
            }
        </style>
    """, unsafe_allow_html=True)
    # ----------------------------------------------------
    # MÀN HÌNH CHÍNH (DASHBOARD KHI CHƯA VÀO THI)
    # ----------------------------------------------------
    if not st.session_state.get("test_mode", False) and not st.session_state.get("test_summary_mode", False):
        st.title("⏱️ Timed Exam Simulator Dashboard")
        st.markdown("---")
        col_left, col_right = st.columns([1.1, 0.9], gap="large")
        
        with col_left:
            # --- KHÔI PHỤC PHẦN SETUP NEW EXAM ---
            st.subheader("🚀 Setup New Exam")
            max_q = len(questions_bank)
            num_q = st.number_input(f"Number of random questions (Max: {max_q}):", min_value=1, max_value=max_q, value=min(3, max_q))
            estimated_minutes = round(num_q * 1.25, 1)
            st.info(f"⏱️ **Allocated Time:** {estimated_minutes} mins for {num_q} questions.")
            
            if st.button("🚀 Start Timed Exam", type="primary", use_container_width=True):
                st.session_state.test_questions = random.sample(questions_bank, num_q)
                st.session_state.test_scores = {}
                st.session_state.test_user_answers = {}  
                st.session_state.test_start_time = time.time()
                st.session_state.test_total_seconds = int(estimated_minutes * 60)
                st.session_state.test_current_idx = 0 
                st.session_state.test_mode = True
                st.session_state.test_summary_mode = False
                st.session_state.test_history_saved = False # 🌟 THÊM DÒNG NÀY: Reset trạng thái lưu cho bài thi mới
                st.rerun()
                
            # --- PHẦN BẢNG LỊCH SỬ ĐA CHỌN & XÓA HÀNG LOẠT ---
            st.markdown("---")
            st.subheader("📊 Exam History Table")
            history_data = load_quiz_history()
            selected_exam_record = None
            
            if history_data:
                history_reversed = history_data[::-1]
                
                df_history = pd.DataFrame([
                    {
                        "Exam Code": item.get("exam_id", "Legacy"), 
                        "Date/Time": item.get("Date/Time", "N/A"), 
                        "Score": item.get("Score", "N/A"), 
                        "Percentage": item.get("Percentage (%)", "N/A"), 
                        "Duration": item.get("Duration", "N/A")
                    } for item in history_reversed
                ])
                
                # Bật tính năng chọn nhiều dòng (multi-row) để vừa dùng được tool tải/tìm kiếm vừa xóa được
                selection_event = st.dataframe(
                    df_history, 
                    use_container_width=True, 
                    hide_index=True, 
                    selection_mode="multi-row", 
                    on_select="rerun"
                )
                
                selected_row_indices = selection_event.get("selection", {}).get("rows", [])
                
                if selected_row_indices:
                    selected_codes = [df_history.iloc[idx]["Exam Code"] for idx in selected_row_indices]
                    
                    # Nếu chỉ chọn 1 dòng duy nhất -> Cho phép hiển thị Review ở Panel phải
                    if len(selected_row_indices) == 1:
                        single_code = selected_codes[0]
                        selected_exam_record = next((item for item in history_reversed if item.get("exam_id") == single_code), None)
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.warning(f"🎯 **Selected {len(selected_codes)} record(s):** `{', '.join(selected_codes)}`")
                    
                    col_space, col_bulk_del = st.columns([1.5, 1])
                    with col_bulk_del:
                        if st.button("🗑️ Delete Selected Rows", type="secondary", use_container_width=True):
                            updated_history = [item for item in history_data if item.get("exam_id") not in selected_codes]
                            save_quiz_history_raw(updated_history)
                            st.success(f"Successfully deleted {len(selected_codes)} record(s)!")
                            st.rerun()
                    with col_space:
                        if len(selected_row_indices) > 1:
                            st.info("💡 You have selected multiple rows. Use the built-in table tools to download or click 'Delete Selected Rows' to remove them completely.")
            else: 
                st.caption("No exam history found yet.")
                
        with col_right:
            st.subheader("🔍 Right-Side Review Panel")
            if selected_exam_record is not None:
                st.markdown(f"### 📋 Details: `{selected_exam_record.get('exam_id')}`")
                st.success(f"**Score:** {selected_exam_record.get('Score')} ({selected_exam_record.get('Percentage (%)')})")
                for idx, q in enumerate(selected_exam_record.get("details", [])):
                    is_correct = (q.get("user_answer") == q.get("correct"))
                    with st.expander(f"{'✅' if is_correct else '❌'} Question {idx + 1}"):
                        st.markdown(f"**Question:** {q['question']}")
                        st.markdown(f"🔹 **Your Choice:** `{q.get('user_answer')}` | 🎯 **Correct:** `{q.get('correct')}`")
                        st.markdown(f"📌 **Mapping:** `{q.get('certification', 'N/A')}` ➔ `{q.get('domain', 'N/A')}`")
                        st.write(f"💡 **AI Explanation:** {q['explanation']}")
            else: 
                st.info("👈 Please select and click any row from the 'Exam History Table' to review.")

    # ----------------------------------------------------
    # CHẾ ĐỘ ĐANG THI (LIVE MOCK EXAM)
    # ----------------------------------------------------
    elif st.session_state.get("test_mode", False) and not st.session_state.get("test_summary_mode", False):
        elapsed_time = time.time() - st.session_state.test_start_time
        remaining_seconds = st.session_state.test_total_seconds - elapsed_time
        
        # Kiểm tra hết giờ chặn trước khi render
        if remaining_seconds <= 0:
            st.error("🚨 **TIME IS UP!**")
            st.session_state.test_mode = False
            st.session_state.test_summary_mode = True
            st.rerun()
            
        # 🛠️ GIẢI PHÁP: Chia cột hàng ngang song song để gom gọn giao diện vào 1 màn hình
        col_title, col_timer = st.columns([1.8, 1.2], vertical_alignment="center")
        
        with col_title:
            # Sử dụng thẻ h2 HTML ép margin về 0 để đẩy sát chữ lên trên đầu
            st.markdown("<h2 style='margin: 0; padding: 0;'>✍️ Live Mock Exam</h2>", unsafe_allow_html=True)
            
        with col_timer:
            # ⏱️ ĐỊNH NGHĨA FRAGMENT: Chạy ngầm cập nhật riêng widget đồng hồ mỗi 1 giây
            @st.fragment(run_every="1s")
            def live_countdown_timer():
                cur_elapsed = time.time() - st.session_state.test_start_time
                cur_remaining = st.session_state.test_total_seconds - cur_elapsed
                
                if cur_remaining <= 0:
                    st.session_state.test_mode = False
                    st.session_state.test_summary_mode = True
                    st.rerun()
                    
                rem_min, rem_sec = int(cur_remaining // 60), int(cur_remaining % 60)
                
                # Đổi màu cảnh báo trực quan
                if cur_remaining < 60:
                    bg_color, text_color, border_color = "#FFEBEE", "#C62828", "#FFCDD2"
                else:
                    bg_color, text_color, border_color = "#E8F5E9", "#2E7D32", "#C8E6C9"
                    
                # Hộp hiển thị bo góc siêu nhỏ gọn (giảm padding từ 12px xuống 8px, font-size 1.15rem)
                st.markdown(f"""
                    <div style="background-color: {bg_color}; border: 1px solid {border_color}; 
                                padding: 8px 12px; border-radius: 8px; text-align: center; margin: 0;">
                        <span style="color: {text_color}; font-size: 1.15rem; font-weight: bold;">
                            ⏱️ TIME: {rem_min:02d}:{rem_sec:02d}
                        </span>
                    </div>
                """, unsafe_allow_html=True)

            # Gọi đồng hồ chạy thực tế bên trong cột bên phải
            live_countdown_timer()
            
        # Đường kẻ mờ phân cách tinh tế với khoảng cách rất hẹp (margin 10px)
        st.markdown("<hr style='margin: 10px 0 15px 0;'>", unsafe_allow_html=True)
                
        idx = st.session_state.test_current_idx
        selected_q = st.session_state.test_questions[idx]
        q_id = selected_q["id"]
        
        st.write(f"**Question {idx + 1} of {len(st.session_state.test_questions)}**")
        st.subheader(selected_q["question"])
        
        is_submitted = q_id in st.session_state.test_user_answers
        
        if is_submitted:
            st.radio("Select your option:", selected_q["options"], index=selected_q["options"].index(st.session_state.test_user_answers[q_id]), key=f"test_view_{q_id}", disabled=True)
            
            user_is_correct = st.session_state.test_scores.get(q_id, False)
            if user_is_correct:
                st.success("🎉 CORRECT!")
                st.markdown(f"""
                <div style="background-color: #E8F5E9; padding: 12px; border-radius: 10px; border-left: 5px solid #4CAF50; margin-top: 10px; margin-bottom: 10px;">
                    <p style="margin: 0; color: #2E7D32;">✅ <b>Keep it up!</b> This question belongs to:<br>🎓 Certification: <code>{selected_q.get('certification', 'N/A')}</code><br>📂 Domain: <code>{selected_q.get('domain', 'N/A')}</code></p>
                </div>""", unsafe_allow_html=True)
            else:
                st.error("❌ INCORRECT! Please try again.")
                st.markdown(f"""
                <div style="background-color: #E3F2FD; padding: 12px; border-radius: 10px; border-left: 5px solid #1E88E5; margin-top: 10px; margin-bottom: 10px;">
                    <p style="margin: 0; color: #333;">📖 <b>Review this concept:</b><br>🎓 Certification: <code>{selected_q.get('certification', 'N/A')}</code><br>📂 Domain: <code>{selected_q.get('domain', 'N/A')}</code></p>
                </div>""", unsafe_allow_html=True)
                
            with st.expander("🔍 View AI Explanation & Source"):
                st.write(selected_q["explanation"])
                st.caption(f"Source: {selected_q['source']} | AI: {selected_q['ai_engine']}")
        else:
            ans = st.radio("Select your option:", selected_q["options"], key=f"test_{q_id}")
            if st.button("Submit Answer"):
                st.session_state.test_user_answers[q_id] = ans
                st.session_state.test_scores[q_id] = (ans == selected_q["correct"])
                st.rerun()
                
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("⬅️ Previous") and idx > 0: 
                st.session_state.test_current_idx -= 1
                st.rerun()
        with col2:
            if idx < len(st.session_state.test_questions) - 1:
                if st.button("Next ➡️"): 
                    st.session_state.test_current_idx += 1
                    st.rerun()
        with col3:
            if st.button("🏁 Submit & Finish", type="primary"):
                st.session_state.test_mode = False
                st.session_state.test_summary_mode = True
                st.rerun()

    # ----------------------------------------------------
    # MÀN HÌNH TỔNG HỢP KẾT QUẢ (SAU KHI SUBMIT & FINISH)
    # ----------------------------------------------------
    elif st.session_state.get("test_summary_mode", False):
        st.title("🏆 Exam Result Summary")
        st.markdown("---")
        
        total_q = len(st.session_state.test_questions)
        correct_ans = sum(1 for q in st.session_state.test_questions if st.session_state.test_scores.get(q["id"]) is True)
        pct = (correct_ans / total_q) * 100
        
        exam_details = [{"id": q["id"], "question": q["question"], "options": q["options"], "correct": q["correct"], "explanation": q["explanation"], "source": q.get("source", "N/A"), "certification": q.get("certification", "N/A"), "domain": q.get("domain", "N/A"), "user_answer": st.session_state.test_user_answers.get(q["id"], "No Answer")} for q in st.session_state.test_questions]
        if not st.session_state.get("test_history_saved", False):
            save_quiz_history(f"{correct_ans} / {total_q}", f"{pct:.2f}%", f"{int((time.time() - st.session_state.test_start_time)//60)}m", exam_details)
            st.session_state.test_history_saved = True # 🌟 Đánh dấu đã lưu thành công để chặn các lượt rerun sau
        
        st.success(f"### Score: {correct_ans} / {total_q} ({pct:.2f}%)")
        
        # --- 📊 PHẦN BIỂU ĐỒ PROGRESS THEO DOMAIN ---
        st.subheader("📊 Domain Progress Distribution")
        from collections import Counter
        domain_counts = Counter([q.get("domain", "N/A") for q in st.session_state.test_questions])
        
        for dom, count in domain_counts.items():
            progress_val = count / total_q
            st.write(f"🔹 **{dom}**: {count} questions")
            st.progress(progress_val)
            
        st.markdown("---")
        
        st.subheader("📝 Detailed Question Review")
        for i, q in enumerate(exam_details):
            is_correct = (q.get("user_answer") == q.get("correct"))
            with st.expander(f"{'✅' if is_correct else '❌'} Question {i + 1}"):
                st.markdown(f"**Question:** {q['question']}")
                st.markdown(f"🔹 **Your Choice:** `{q.get('user_answer')}` | 🎯 **Correct:** `{q.get('correct')}`")
                st.markdown(f"📌 **Mapping:** `{q.get('certification', 'N/A')}` ➔ `{q.get('domain', 'N/A')}`")
                st.write(f"💡 **AI Explanation:** {q['explanation']}")
                
        st.markdown("---")
        
        if st.button("🔄 Back to Exam Dashboard", type="primary", use_container_width=True):
            st.session_state.test_mode = False
            st.session_state.test_summary_mode = False
            if "test_questions" in st.session_state: del st.session_state.test_questions
            st.rerun()

# ==========================================
# 📊 PHẦN 5: PERFORMANCE DASHBOARD
# ==========================================
elif menu_choice == "📊 Performance Dashboard":
    st.title("📊 Performance & AI Insights Dashboard")
    st.markdown("---")
    
    history_data = load_quiz_history()
    if not history_data:
        st.info("💡 No exam data available yet!")
    else:
        processed_records = []
        wrong_topics_count = {}
        total_questions_attempted = 0
        total_correct_answers = 0
        
        # Cấu trúc lưu trữ phân tích động theo từng Domain giống mẫu image_ee8a08.png
        domain_stats = {}
        
        for item in history_data:
            pct_val = float(item.get("Percentage (%)", "0%").replace("%", ""))
            processed_records.append({"Date": item.get("Date/Time", "N/A"), "Score (%)": pct_val})
            
            for q in item.get("details", []):
                total_questions_attempted += 1
                
                # Xác định tên Domain/Topic của câu hỏi
                domain_name = q.get("domain") or q.get("topic") or "Uncategorized"
                if domain_name not in domain_stats:
                    domain_stats[domain_name] = {"correct": 0, "incorrect": 0}
                
                # Tính toán Đúng / Sai
                if q.get("user_answer") == q.get("correct"): 
                    total_correct_answers += 1
                    domain_stats[domain_name]["correct"] += 1
                else:
                    domain_stats[domain_name]["incorrect"] += 1
                    # Giữ nguyên logic tính toán lỗi sai cho AI Suggestion của bạn
                    src = q.get("source", "General PMP")
                    wrong_topics_count[src] = wrong_topics_count.get(src, 0) + 1
                    
        df_metrics = pd.DataFrame(processed_records)
        
        # --- HIỂN THỊ CỤM METRICS TỔNG QUAN ---
        col1, col2, col3 = st.columns(3)
        with col1: st.metric("Total Attempts", len(df_metrics))
        with col2: st.metric("Average Score", f"{df_metrics['Score (%)'].mean():.1f}%")
        with col3: st.metric("Overall Accuracy", f"{(total_correct_answers/total_questions_attempted*100) if total_questions_attempted > 0 else 0:.1f}%")
        
        st.markdown("---")
        
        # --- CHIA HAI CỘT: BIỂU ĐỒ XU HƯỚNG & AI SUGGESTION ---
        c_chart, c_ai = st.columns([1.1, 0.9], gap="large")
        with c_chart:
            st.subheader("📈 Score Progression Trend")
            st.line_chart(df_metrics.copy().set_index("Date")["Score (%)"])
            
        with c_ai:
            st.subheader("🤖 AI Learning & Weakness Analyzer")
            if not wrong_topics_count: 
                st.success("No mistakes recorded yet!")
            else:
                sorted_topics = sorted(wrong_topics_count.items(), key=lambda x: x[1], reverse=True)
                st.warning(f"Focus Area: **{sorted_topics[0][0]}** (Failed {sorted_topics[0][1]} times)")
                st.info("Action Plan: Review the associated core sections in the Knowledge Hub or deep-dive into the raw question descriptions.")
                
        st.markdown("---")
        
        # --- TÍCH HỢP BẢNG THỐNG KÊ ĐÚNG/SAI THEO DOMAIN (Chuẩn image_ee8a08.png) ---
        st.subheader("📋 All Topics Breakdown")
        
        # Thiết lập tiêu đề bảng chia cột
        h_col1, h_col2, h_col3, h_col4, h_col5 = st.columns([2.5, 0.8, 0.8, 1.2, 1.2])
        with h_col1: st.markdown("**Topic / Domain**")
        with h_col2: st.markdown("<p style='color:#2E7D32; font-weight:bold; text-align:center; margin:0;'>Correct</p>", unsafe_allow_html=True)
        with h_col3: st.markdown("<p style='color:#C62828; font-weight:bold; text-align:center; margin:0;'>Incorrect</p>", unsafe_allow_html=True)
        with h_col4: st.markdown("**Questions Answered**")
        with h_col5: st.markdown("**Mastery Level**")
        st.markdown("<hr style='margin: 5px 0 12px 0;'>", unsafe_allow_html=True)
        
        # Đổ dữ liệu phân tích từng hàng vào bảng
        for dom, stats in domain_stats.items():
            correct_cnt = stats["correct"]
            incorrect_cnt = stats["incorrect"]
            total_dom_q = correct_cnt + incorrect_cnt
            
            # Tính phần trăm chính xác của từng Domain
            accuracy = (correct_cnt / total_dom_q) * 100 if total_dom_q > 0 else 0
            
            # Đổi màu Badge số phần trăm động linh hoạt theo kết quả đạt được
            if accuracy >= 75:
                badge_color, text_color = "#E8F5E9", "#2E7D32"  # Xanh lá khi kết quả tốt
            elif accuracy >= 50:
                badge_color, text_color = "#FFF3E0", "#E65100"  # Cam khi kết quả trung bình
            else:
                badge_color, text_color = "#FFEBEE", "#C62828"  # Đỏ khi cần cải thiện
                
            r_col1, r_col2, r_col3, r_col4, r_col5 = st.columns([2.5, 0.8, 0.8, 1.2, 1.2])
            
            with r_col1:
                st.markdown(f"🔹 **{dom}**")
            with r_col2:
                st.markdown(f"<p style='text-align:center; color:#2E7D32; font-weight:bold; margin:0;'>{correct_cnt}</p>", unsafe_allow_html=True)
            with r_col3:
                st.markdown(f"<p style='text-align:center; color:#C62828; font-weight:bold; margin:0;'>{incorrect_cnt}</p>", unsafe_allow_html=True)
            with r_col4:
                # Hiển thị số lượng câu Đúng / Tổng số câu đã làm kèm highlight xanh dương đậm nét
                st.markdown(f"<p style='margin:0;'><b>{accuracy:.0f}%</b> ({correct_cnt}/{total_dom_q})</p>", unsafe_allow_html=True)
            with r_col5:
                # Hiển thị Badge phần trăm bo góc kèm thanh tiến độ đồng bộ
                st.markdown(f"""
                <div style="background-color: {badge_color}; padding: 1px 6px; border-radius: 5px; text-align: center; display: inline-block; min-width: 50px; margin-bottom: 2px;">
                    <span style="color: {text_color}; font-weight: bold; font-size: 13px;">{accuracy:.0f}%</span>
                </div>
                """, unsafe_allow_html=True)
                st.progress(accuracy / 100)
                
            st.markdown("<hr style='margin: 6px 0;'>", unsafe_allow_html=True)

# ==========================================================
# 🤖 PHẦN 6: AI TUTOR CHAT (HỖ TRỢ ONLINE GEMINI & OFFLINE ENGINE)
# ==========================================================
elif menu_choice == "🤖 AI Tutor Chat":
    st.title("🤖 AI Tutor Chat Expert")
    st.markdown("##### *Your 24/7 Project Management Assistant for PMP® & CAPM® Success*")
    st.markdown("---")

    # 1. Khởi tạo lịch sử chat trong session_state nếu chưa có
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # 2. Định nghĩa bộ từ điển dữ liệu PMP để chạy Offline Match Engine phòng hờ
    offline_pmp_data = {
        "predictive planning": (
            "**[Offline Tutor Insights]**\n\n"
            "* **Predictive Approach (Waterfall):** Scope, Time, and Cost are frozen during Planning phase.\n"
            "* **Control:** Future modifications must undergo a formal change control process via the CCB."
        ),
        "agile": (
            "**[Offline Tutor Insights]**\n\n"
            "* **Agile Approach (Adaptive):** Iterative and incremental delivery. Scope is decomposed into a Product Backlog.\n"
            "* **Roles:** Product Owner manages backlog, Scrum Master removes impediments, Team delivers value."
        ),
        "hybrid": (
            "**[Offline Tutor Insights]**\n\n"
            "* **Hybrid Approach:** A combination of predictive and adaptive strategies.\n"
            "* **Execution:** Often uses predictive for clear requirements (e.g., hardware) and Agile for uncertain components (e.g., software)."
        )
    }

    # 3. Hiển thị lịch sử các câu thoại trước đó (nếu có)
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # 4. Nhận câu hỏi đầu vào từ người dùng thông qua khung chat st.chat_input
    if user_prompt := st.chat_input("Ask me any PMP situation, formulas, or process concepts..."):
        
        # Hiển thị câu hỏi của người dùng ngay lập tức lên màn hình
        with st.chat_message("user"):
            st.markdown(user_prompt)
        
        # Lưu câu hỏi vào lịch sử chat
        st.session_state.chat_history.append({"role": "user", "content": user_prompt})

        # XỬ LÝ PHẢN HỒI TỪ AI TUTOR
        with st.chat_message("assistant"):
            # KỊCH BẢN A: GỌI API TRỰC TUYẾN (Dựa theo nhà cung cấp được chọn)
            if active_api_key:
                # ---- 1. CẤU HÌNH & GỌI GOOGLE GEMINI ----
                if api_provider == "Google Gemini":
                    try:
                        import google.generativeai as genai
                        genai.configure(api_key=active_api_key)
                        model = genai.GenerativeModel('models/gemini-2.5-flash')
                        
                        system_context = (
                            "You are an expert PMP and CAPM Tutor. Answer the user's question professionally, "
                            "referencing PMBOK Guide 7th Edition, Agile Practice Guide, The PMI guide to Business Analysis, Scrum master, or Process Groups Practice Guide, Agile guide practice, Effective project management: Trandition, Agile, extreme, hybrid, eigth edition, Project management answer book 2nd edition, PMP project management professional practice tests 2021 exam update, PM illustrated: A visual learners' guide to project management. "
                            "Provide structured, clear, and easy-to-understand explanations. You must define reliable sources for your answers, ideally citing specific sections from any materials when relevant. "
                        )
                        with st.spinner("Gemini is thinking..."):
                            response = model.generate_content(f"{system_context}\n\nUser Question: {user_prompt}")
                            ai_response = response.text
                        st.markdown(ai_response)
                        st.session_state.chat_history.append({"role": "assistant", "content": ai_response})
                    except Exception as e:
                        st.error(f"❌ Gemini API Error: {str(e)}")

                # ---- 2. CẤU HÌNH & GỌI OPENAI (Kích hoạt khi người dùng nhập Key chính xác) ----
                elif api_provider == "OpenAI":
                    try:
                        from openai import OpenAI
                        # Khởi tạo client với key người dùng cung cấp
                        client = OpenAI(api_key=active_api_key)
                        
                        with st.spinner("ChatGPT is thinking..."):
                            response = client.chat.completions.create(
                                model="gpt-4o-mini", # Sử dụng dòng model gpt-4o-mini tối ưu, tiết kiệm chi phí cho user
                                messages=[
                                    {"role": "system", "content": "You are an expert PMP and CAPM Tutor. Answer the user's question professionally,referencing PMBOK Guide 7th Edition, Agile Practice Guide, The PMI guide to Business Analysis, Scrum master, or Process Groups Practice Guide, Agile guide practice, Effective project management: Trandition, Agile, extreme, hybrid, eigth edition, Project management answer book 2nd edition, PMP project management professional practice tests 2021 exam update, PM illustrated: A visual learners' guide to project management. Provide structured, clear, and easy-to-understand explanations. You must define reliable sources for your answers, ideally citing specific sections from any materials when relevant."},
                                    {"role": "user", "content": user_prompt}
                                ]
                            )
                            ai_response = response.choices[0].message.content
                        st.markdown(ai_response)
                        st.session_state.chat_history.append({"role": "assistant", "content": ai_response})
                    except Exception as e:
                        st.error(f"❌ OpenAI API Error: {str(e)}")

                # ---- 3. CẤU HÌNH & GỌI ANTHROPIC CLAUDE (Kích hoạt khi người dùng nhập Key chính xác) ----
                elif api_provider == "Anthropic Claude":
                    try:
                        from anthropic import Anthropic
                        # Khởi tạo client Anthropic với key người dùng cung cấp
                        client = Anthropic(api_key=active_api_key)
                        
                        with st.spinner("Claude is thinking..."):
                            response = client.messages.create(
                                model="claude-3-5-haiku-20241022", # Sử dụng model Haiku tốc độ cao và tối ưu chi phí
                                max_tokens=1024,
                                system="You are an expert PMP and CAPM Tutor. Answer the user's question professionally,referencing PMBOK Guide 7th Edition, Agile Practice Guide, The PMI guide to Business Analysis, Scrum master, or Process Groups Practice Guide, Agile guide practice, Effective project management: Trandition, Agile, extreme, hybrid, eigth edition, Project management answer book 2nd edition, PMP project management professional practice tests 2021 exam update, PM illustrated: A visual learners' guide to project management. Provide structured, clear, and easy-to-understand explanations. You must define reliable sources for your answers, ideally citing specific sections from any materials when relevant.",
                                messages=[
                                    {"role": "user", "content": user_prompt}
                                ]
                            )
                            ai_response = response.content[0].text
                        st.markdown(ai_response)
                        st.session_state.chat_history.append({"role": "assistant", "content": ai_response})
                    except Exception as e:
                        st.error(f"❌ Anthropic API Error: {str(e)}")
            
            # KỊCH BẢN B: CHẠY ENGINE OFFLINE DỰ PHÒNG KHI KHÔNG CÓ KEY
            else:
                st.markdown("*(💡 API Key is missing. Please enter your key in the sidebar. Falling back to offline match engine)*")
                
                # Biến đổi câu hỏi thành chữ thường để khớp từ khóa chính xác hơn
                search_query = user_prompt.lower()
                matched_content = None
                
                # Quét xem từ khóa trong câu hỏi có nằm trong bộ từ điển cứu cánh không
                for keyword, insight in offline_pmp_data.items():
                    if keyword in search_query:
                        matched_content = insight
                        break
                
                if matched_content:
                    st.markdown(matched_content)
                    st.session_state.chat_history.append({"role": "assistant", "content": matched_content})
                else:
                    no_key_warning = (
                        "**[Offline Tutor Insights]**\n\n"
                        "Hệ thống chưa tìm thấy từ khóa tương ứng trong bộ nhớ offline.\n\n"
                        "⚠️ **Để nhận được câu trả lời thông minh, chuyên sâu và linh hoạt cho mọi tình huống PMP**, "
                        "bạn hãy chuyển cấu hình **AI Provider sang Google Gemini** ở Sidebar bên trái "
                        "để kích hoạt gói API Free chạy tự động nhé!"
                    )
                    st.markdown(no_key_warning)
                    st.session_state.chat_history.append({"role": "assistant", "content": no_key_warning})

    # Nút bấm tiện ích xóa sạch lịch sử hội thoại để chat lại từ đầu
    if st.session_state.chat_history:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🗑️ Clear Chat History"):
            st.session_state.chat_history = []
            st.rerun()