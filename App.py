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

# ==========================================
# 🔌 ĐỌC/GHI DỮ LIỆU TỪ FILE JSON NGOÀI
# ==========================================
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

def load_quiz_history():
    file_name = "quiz_history.json"
    if os.path.exists(file_name):
        with open(file_name, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

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
def save_quiz_history_raw(updated_list):
    """Hàm ghi đè danh sách lịch sử mới sau khi đã xóa dòng vào file JSON"""
    import json
    # Thay 'quiz_history.json' bằng đúng tên file lưu lịch sử thực tế trong code của bạn
    with open("quiz_history.json", "w", encoding="utf-8") as f:
        json.dump(updated_list, f, ensure_ascii=False, indent=4)

# 💡 ĐÂY LÀ HÀM BẠN ĐANG BỊ THIẾU - HÃY THÊM NÓ VÀO ĐÂY:
def load_knowledge_from_json():
    file_name = "knowledge_hub.json"
    if os.path.exists(file_name):
        try:
            with open(file_name, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

# Nạp ngân hàng câu hỏi gốc
questions_bank = load_questions_from_json()
# ==========================================
# 📑 KHỔI TẠO CÁC BIẾN BỘ NHỚ (SESSION STATE)
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


# ==========================================
# 🧭 PHẦN 1: THANH ĐIỀU HƯỚNG & CẤU HÌNH API MULTI-LLM
# ==========================================
st.sidebar.title("🎯 PMP/CAPM Learning Hub")

menu_choice = st.sidebar.radio(
    "Choose a feature:",
    ["📚 Knowledge Hub", "📝 Question Bank", "⏱️ Exam Simulator", "📊 Performance Dashboard", "🤖 AI Tutor Chat"]
)

st.sidebar.markdown("---")
st.sidebar.subheader("🔑 Live AI Engine Settings")
# 🌟 Đã bổ sung Anthropic Claude vào danh sách lựa chọn
api_provider = st.sidebar.selectbox("AI Provider:", ["Google Gemini", "OpenAI", "Anthropic Claude"])
api_key = st.sidebar.text_input("Enter your API Key:", type="password", help="Key chỉ lưu tạm trong RAM phiên làm việc của trình duyệt.")

if menu_choice == "📝 Question Bank" and not st.session_state.bank_finished:
    st.sidebar.markdown("---")
    st.sidebar.subheader("🗂️ Bank Navigator")
    bank_labels = [f"Question {i+1} {'✅' if q['id'] in st.session_state.bank_scores and st.session_state.bank_scores[q['id']] else '❌' if q['id'] in st.session_state.bank_scores else '⏳'}" for i, q in enumerate(questions_bank)]
    chosen_bank_idx = st.sidebar.radio("Jump to any question:", options=range(len(questions_bank)), format_func=lambda x: bank_labels[x], index=st.session_state.bank_current_idx)
    if chosen_bank_idx != st.session_state.bank_current_idx:
        st.session_state.bank_current_idx = chosen_bank_idx
        st.rerun()

elif menu_choice == "⏱️ Exam Simulator" and st.session_state.test_mode:
    st.sidebar.markdown("---")
    st.sidebar.subheader("🧩 Exam Navigator")
    test_labels = [f"Question {i+1} {'✅' if q['id'] in st.session_state.test_user_answers and st.session_state.test_scores.get(q['id']) else '❌' if q['id'] in st.session_state.test_user_answers else '⏳'}" for i, q in enumerate(st.session_state.test_questions)]
    chosen_test_idx = st.sidebar.radio("Jump to exam question:", options=range(len(st.session_state.test_questions)), format_func=lambda x: test_labels[x], index=st.session_state.test_current_idx)
    if chosen_test_idx != st.session_state.test_current_idx:
        st.session_state.test_current_idx = chosen_test_idx
        st.rerun()

st.sidebar.markdown("---")
st.sidebar.caption("Version 7.3 | Multi-LLM (Gemini / OpenAI / Claude)")

# ==========================================
# 📚PHẦN 2: KNOWLEDGE HUB (MINIMALIST STYLE - VERSION 12.0)
# ==========================================
if menu_choice == "📚 Knowledge Hub":
    st.title("📚 Professional Certification Knowledge Hub")
    
    # CSS Tùy chỉnh: Sidebar Pastel Blue và Card tối giản
    st.markdown("""
        <style>
        /* Tô màu Sidebar */
        [data-testid="stSidebar"] {
            background-color: #E3F2FD; /* Pastel Blue */
        }
        
        /* Card tối giản, đồng nhất */
        .task-card {
            background-color: #FFFFFF;
            color: #333333;
            border: 1px solid #D1D9E0;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        }
        
        /* Dark Mode Override */
        @media (prefers-color-scheme: dark) {
            .task-card {
                background-color: #262730;
                color: #FFFFFF;
                border: 1px solid #444;
            }
        }
        </style>
    """, unsafe_allow_html=True)

    eco_data = load_knowledge_from_json()

    cert_structure = {
        "PMP": ["People", "Process", "Business Environment"],
        "CAPM": ["Project Management Fundamentals and Core Concepts", 
                 "Predictive, Plan-Based Methodologies", 
                 "Agile Frameworks/Methodologies", 
                 "Business Analysis Frameworks"]
    }

    # Chọn Chứng chỉ
    st.write("") # Tạo khoảng trống nhỏ
    cert_select = st.radio("Select Certification:", list(cert_structure.keys()), horizontal=True)
    
    # Layout sidebar giả lập (Vertical Menu)
    col_menu, col_content = st.columns([1, 3])
    
    with col_menu:
        selected_domain = st.radio("Select Domain:", cert_structure[cert_select])

    with col_content:
        st.subheader(f"📖 {selected_domain}")
        tasks = [t for t in eco_data if t.get("domain") == selected_domain]
        
        if not tasks:
            st.info("No tasks found for this domain.")
        else:
            # Từ điển định nghĩa bảng màu Pastel cho từng loại Approach
            approach_colors = {
                "PREDICTIVE": {"bg": "#E3F2FD", "text": "#0D47A1"},  # Xanh dương nhẹ
                "AGILE": {"bg": "#E8F5E9", "text": "#41B67C"},    # Xanh lá nhẹ
                "BOTH": {"bg": "#F3E5F5", "text": "#4A148C"}        # Tím nhạt
            }

            for t_data in tasks:
                # Chuẩn hóa chuỗi dữ liệu approach đầu vào
                raw_approach = str(t_data.get('approach', '')).upper().strip()
                
                # Lấy cấu hình màu tương ứng (Mặc định dùng cấu hình BOTH nếu không khớp)
                color_cfg = approach_colors.get(raw_approach, approach_colors["BOTH"])
                
                # Tạo chuỗi thẻ Span HTML chứa style Badge Pastel tạo điểm nhấn
                approach_badge_html = f"""
                <span style="
                    background-color: {color_cfg['bg']}; 
                    color: {color_cfg['text']}; 
                    padding: 2px 10px; 
                    border-radius: 6px; 
                    font-weight: bold; 
                    font-size: 0.85em;
                    display: inline-block;
                    border: 1px solid {color_cfg['text']}20;
                ">
                    {raw_approach}
                </span>
                """

                # Render Card hoàn thiện kết hợp Badge HTML động vào vị trí cũ
                st.markdown(f"""
                    <div class="task-card">
                        <div style="font-weight: bold; font-size: 1.2em; color: #1E88E5; margin-bottom: 10px;">
                            Task {t_data.get('task_number', '')}: {t_data.get('task', 'Untitled')}
                        </div>
                        <div style="line-height: 1.6;">
                            <b>Approach:</b> {approach_badge_html}<br>
                            <div style="margin-top: 6px;"><b>Summary:</b> {t_data.get('summary', 'N/A')}</div>
                            <b>Key Concepts:</b> {', '.join(t_data.get('key_concepts', []))}
                        </div>
                        <div style="background-color: #F5F5F5; color: #555; padding: 10px; border-radius: 8px; margin-top: 15px; font-size: 0.9em;">
                            💡 <b>Exam Tip:</b> {t_data.get('exam_tips', 'N/A')}
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                

# ==========================================
# 📝 PHẦN 3: QUESTION BANK
# ==========================================
elif menu_choice == "📝 Question Bank":
    st.title("📝 Question Bank Practice")
    st.markdown("---")
    
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
                # st.rerun() # Bỏ comment nếu muốn tự động làm mới
        
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
                        st.caption(f"Source: {q['source']} | AI: {q['ai_engine']}")
            else: 
                st.info("👈 Please select and click any row from the 'Exam History Table' to review.")

    # ----------------------------------------------------
    # CHẾ ĐỘ ĐANG THI (LIVE MOCK EXAM)
    # ----------------------------------------------------
    elif st.session_state.get("test_mode", False) and not st.session_state.get("test_summary_mode", False):
        elapsed_time = time.time() - st.session_state.test_start_time
        remaining_seconds = st.session_state.test_total_seconds - elapsed_time
        if remaining_seconds <= 0:
            st.error("🚨 **TIME IS UP!**")
            st.session_state.test_mode = False
            st.session_state.test_summary_mode = True
            st.rerun()
            
        rem_min, rem_sec = int(remaining_seconds // 60), int(remaining_seconds % 60)
        st.title(f"✍️ Live Mock Exam | ⏱️ {rem_min:02d}:{rem_sec:02d}")
        
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
        save_quiz_history(f"{correct_ans} / {total_q}", f"{pct:.2f}%", f"{int((time.time() - st.session_state.test_start_time)//60)}m", exam_details)
        
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

# ==========================================
# 🤖 PHẦN 6: AI TUTOR CHAT (HỖ TRỢ TRỰC TIẾP GEMINI / OPENAI / CLAUDE)
# ==========================================
elif menu_choice == "🤖 AI Tutor Chat":
    st.title("🤖 Chat with PMP/CAPM AI Tutor")
    st.markdown("Hệ thống giải đáp học thuật đa mô hình. Toàn bộ phản hồi từ AI sẽ bắt buộc xuất ra bằng **Tiếng Anh**.")
    st.markdown("---")
    
    # Hiển thị lịch sử chat
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            
    # Ô nhập câu hỏi chuẩn chat_input
    if user_prompt := st.chat_input("Ask any project management question here..."):
        with st.chat_message("user"):
            st.write(user_prompt)
        st.session_state.chat_history.append({"role": "user", "content": user_prompt})
        
        with st.chat_message("assistant"):
            with st.spinner(f"AI Tutor ({api_provider}) is analyzing..."):
                
                # Khởi tạo Prompt hệ thống chuẩn hóa
                system_content = (
                    "You are an elite PMP and CAPM exam tutor. Answer the user's questions strictly "
                    "following the PMBOK Guide (both 6th and 7th editions) and Process Groups Practice Guide. "
                    "Keep explanations highly structured, professional, and actionable. Use bullet points. "
                    "CRITICAL REQUIREMENT: You must always respond in English, regardless of the language "
                    "used by the user (even if the user asks in Vietnamese or any other language)."
                )
                
                # TRƯỜNG HỢP 1: Có API Key đầy đủ
                if api_key:
                    try:
                        # 🌟 NHÁNH MỚI: Xử lý Anthropic Claude (Giao tiếp REST API nguyên bản)
                        if api_provider == "Anthropic Claude":
                            claude_messages = []
                            for msg in st.session_state.chat_history:
                                if msg["role"] in ["user", "assistant"]:
                                    claude_messages.append({"role": msg["role"], "content": msg["content"]})
                            
                            headers = {
                                "x-api-key": api_key,
                                "anthropic-version": "2023-06-01",
                                "content-type": "application/json"
                            }
                            payload = {
                                "model": "claude-3-5-sonnet-20241022",
                                "max_tokens": 2048,
                                "system": system_content,
                                "messages": claude_messages,
                                "temperature": 0.3
                            }
                            res = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload)
                            if res.status_code == 200:
                                ai_response = res.json()["content"][0]["text"]
                            else:
                                err_msg = res.json().get("error", {}).get("message", res.text)
                                ai_response = f"❌ **Claude API Error:** {err_msg}"
                        
                        # 🌟 NHÁNH CŨ: Xử lý OpenAI & Google Gemini (Thông qua thư viện SDK)
                        elif OPENAI_AVAILABLE:
                            if api_provider == "Google Gemini":
                                client = OpenAI(
                                    api_key=api_key,
                                    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
                                )
                                model_engine = "gemini-2.5-flash"
                            else:
                                client = OpenAI(api_key=api_key)
                                model_engine = "gpt-4o-mini"
                            
                            messages_payload = [{"role": "system", "content": system_content}]
                            for msg in st.session_state.chat_history:
                                messages_payload.append({"role": msg["role"], "content": msg["content"]})
                                
                            api_call = client.chat.completions.create(
                                model=model_engine,
                                messages=messages_payload,
                                temperature=0.3
                            )
                            ai_response = api_call.choices[0].message.content
                        else:
                            ai_response = "❌ **Library Error:** `openai` package is missing. Cannot route request to OpenAI/Gemini."
                            
                    except Exception as err:
                        ai_response = f"❌ **API Connection Error:** {str(err)}.\nPlease check your API Key and Provider settings."
                
                # TRƯỜNG HỢP 2: Chế độ Offline cứu hộ khi chưa điền Key
                else:
                    time.sleep(0.5)
                    low_prompt = user_prompt.lower()
                    offline_warning = "*(💡 API Key is missing. Please enter your key in the sidebar. Falling back to offline match engine)*\n\n"
                        
                    if "agile" in low_prompt or "linh hoạt" in low_prompt:
                        ai_response = offline_warning + """**[Offline Tutor Insights]** \n* **Agile Approach:** Focuses on adaptive, iterative lifecycles (Sprints usually lasting 1-4 weeks). \n* **Key Frameworks:** Scrum, Kanban, XP.\n* **Exam Tip:** Choose Agile/Hybrid options when requirements are volatile."""
                    elif "waterfall" in low_prompt or "thác nước" in low_prompt or "predictive" in low_prompt:
                        ai_response = offline_warning + """**[Offline Tutor Insights]** \n* **Predictive Approach (Waterfall):** Scope, Time, and Cost are frozen during Planning phase.\n* **Control:** Future modifications must undergo a formal change control process via the CCB."""
                    else:
                        ai_response = offline_warning + f"**[Offline Tutor Insights]** Received: *\"{user_prompt}\"*.\n\nPlease configure your **{api_provider} API Key** in the sidebar to fetch a direct online explanation in English!"
                
                # In kết quả lên màn hình và lưu vào bộ nhớ
                st.write(ai_response)
                st.session_state.chat_history.append({"role": "assistant", "content": ai_response})
                
        st.rerun()