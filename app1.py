import json
import streamlit as st
from openai import OpenAI
import streamlit.components.v1 as components
from datetime import datetime, timezone, timedelta

# ================== 1. CẤU HÌNH TRANG & GIAO DIỆN ==================
st.set_page_config(page_title="LSA Translator | Groq + DeepSeek", page_icon="🌊", layout="centered")

st.markdown("""
    <style>
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    .groq-title-container { text-align: center; margin-bottom: 30px; padding-bottom: 20px; border-bottom: 1px solid #333; }
    .groq-title {
        font-size: 2.8rem; font-weight: 900;
        background: linear-gradient(90deg, #00b4ff, #0090cc);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin-bottom: 5px; letter-spacing: -1px;
    }
    .groq-subtitle { color: #888; font-size: 1.1rem; font-weight: 400; }

    div[data-testid="stFormSubmitButton"] > button {
        background: linear-gradient(90deg, #00b4ff, #0090cc) !important;
        color: white !important; border: none !important; border-radius: 8px !important;
        font-weight: bold !important; font-size: 16px !important;
    }
    div[data-testid="stFormSubmitButton"] > button:hover {
        transform: translateY(-2px); box-shadow: 0 6px 20px rgba(0, 180, 255, 0.5) !important;
    }

    .result-header { font-size: 18px; font-weight: bold; color: #00b4ff; display: flex; align-items: center; gap: 8px; margin-top: 10px;}

    footer {visibility: hidden;}
    .stTextArea textarea { font-size: 15.5px !important; border-radius: 8px; }
    </style>
""", unsafe_allow_html=True)


# ================== RENDER RESULT BOX (FIX COPY + FIX HEIGHT + FIX THEME) ==================
def render_result_box(placeholder, label, text):
    """
    Render result box bên trong components.html() để có quyền clipboard-write.
    - Height: Cải thiện công thức tính hào phóng hơn để không bị cắt chữ.
    - Theme: Hardcode dark style, không phụ thuộc Streamlit theme setting.
    - Khung linh hoạt: Bật overflow-y và custom thanh cuộn phòng hờ nội dung siêu dài.
    """
    safe_text = json.dumps(text)

    # Chia dòng an toàn hơn (giảm xuống 22 ký tự/dòng để bao trọn các từ bị rớt dòng)
    CHARS_PER_LINE = 22
    lines = text.split('\n')
    total_lines = sum((len(line) // CHARS_PER_LINE) + 1 for line in lines)
    
    # Tính toán chiều cao thoải mái (tăng buffer lên 100px)
    height = max(180, 40 + 32 + (total_lines * 28) + 100)

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        /* Force dark — không để Streamlit theme ảnh hưởng */
        html, body {{
            background: transparent !important;
            /* Đổi từ hidden sang auto để cho phép cuộn nếu vượt quá khung */
            overflow-y: auto;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }}
        
        /* Tùy chỉnh thanh cuộn cho thanh lịch, hợp với dark theme */
        ::-webkit-scrollbar {{ width: 6px; }}
        ::-webkit-scrollbar-track {{ background: transparent; }}
        ::-webkit-scrollbar-thumb {{ background: #444; border-radius: 10px; }}
        ::-webkit-scrollbar-thumb:hover {{ background: #00b4ff; }}

        .result-box {{
            background: #1e1e1e !important;
            color: #f0f0f0 !important;
            padding: 16px 50px 16px 18px;
            border-radius: 12px;
            border-left: 4px solid #00b4ff;
            border-top: 1px solid #3a3a3a;
            border-right: 1px solid #3a3a3a;
            border-bottom: 1px solid #3a3a3a;
            font-size: 15px;
            line-height: 1.65;
            word-break: break-word;
            position: relative;
            margin: 4px 0 8px 0;
            min-height: 100%;
        }}
        .label {{
            font-weight: 700;
            color: #00b4ff !important;
            font-size: 15px;
            margin-bottom: 10px;
            display: block;
        }}
        .content {{
            color: #f0f0f0 !important;
            line-height: 1.65;
            white-space: pre-wrap;
            word-break: break-word;
        }}
        .hover-btn {{
            position: absolute;
            top: 12px;
            right: 12px;
            background: rgba(0, 180, 255, 0.15);
            color: #00b4ff;
            border: 1px solid rgba(0,180,255,0.2);
            border-radius: 6px;
            width: 34px;
            height: 34px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            opacity: 0;
            transition: opacity 0.2s ease, transform 0.15s ease;
            font-size: 16px;
        }}
        .result-box:hover .hover-btn {{ opacity: 1; }}
        .hover-btn:hover {{
            background: rgba(0, 180, 255, 0.3);
            transform: scale(1.1);
        }}
    </style>
    </head>
    <body>
    <div class="result-box" id="box">
        <span class="label">{label}</span>
        <div class="content" id="content"></div>
        <button class="hover-btn" id="copyBtn" onclick="copyText()" title="Copy">📋</button>
    </div>
    <script>
        document.getElementById('content').textContent = {safe_text};

        function copyText() {{
            var btn = document.getElementById('copyBtn');
            var textVal = {safe_text};
            if (navigator.clipboard && navigator.clipboard.writeText) {{
                navigator.clipboard.writeText(textVal).then(function() {{
                    btn.innerHTML = '✅';
                    setTimeout(function() {{ btn.innerHTML = '📋'; }}, 1800);
                }}).catch(function() {{ fallbackCopy(textVal, btn); }});
            }} else {{
                fallbackCopy(textVal, btn);
            }}
        }}

        function fallbackCopy(text, btn) {{
            var ta = document.createElement('textarea');
            ta.value = text;
            ta.style.position = 'fixed';
            ta.style.left = '-9999px';
            ta.style.top  = '-9999px';
            document.body.appendChild(ta);
            ta.focus(); ta.select();
            try {{
                document.execCommand('copy');
                btn.innerHTML = '✅';
            }} catch(e) {{
                btn.innerHTML = '❌';
            }}
            setTimeout(function() {{ btn.innerHTML = '📋'; }}, 1800);
            document.body.removeChild(ta);
        }}
    </script>
    </body>
    </html>
    """
    placeholder.empty()
    with placeholder:
        # Bật scrolling=True để nếu nội dung quá dài, nó sẽ xuất hiện thanh cuộn đẹp mắt thay vì ẩn mất chữ
        components.html(html_content, height=height, scrolling=True)


# ================== 2. CẤU HÌNH 2 API ==================
groq_client = OpenAI(api_key=st.secrets["GROQ_API_KEY"], base_url="https://api.groq.com/openai/v1")
GROQ_MODEL = "llama-3.3-70b-versatile"

deepseek_client = OpenAI(api_key=st.secrets["DEEPSEEK_API_KEY"], base_url="https://api.deepseek.com")
DEEPSEEK_MODEL = "deepseek-chat"

# ================== 3. TỪ ĐIỂN ==================
DICT_JP_VI = {
    "レタッチ": "Retouch",
    "加筆する": "Vẽ bù / Vẽ thêm",
    "写植": "Lettering (Shashoku)",
    "ゴミ取り": "Làm sạch (Gomitori)",
    "非表示レイヤー": "Layer ẩn",
    "フォルダ": "Folder",
    "グループ": "Group",
    "インペイント": "Inpainting",
    "削除補完": "Inpainting",
    "スクリプト": "Script",
    "パツンパツン": "Quá tải / Bận kẹt lịch",
    "パツパツ": "Quá tải / Bận kẹt lịch",
    "単行本": "Truyện dài / Tankoubon",
    "読切": "Truyện ngắn / Yomikiri"
}
dict_prompt_str = "\n".join([f"- {k} -> {v}" for k, v in DICT_JP_VI.items()])

# ================== 4. SESSION STATE ==================
if "is_jp_to_vi" not in st.session_state:
    st.session_state.is_jp_to_vi = False
if "main_input" not in st.session_state:
    st.session_state["main_input"] = ""
if "history" not in st.session_state:
    st.session_state.history = []
# Lưu kết quả dịch để re-render sau khi rerun
if "last_groq" not in st.session_state:
    st.session_state.last_groq = ""
if "last_deep" not in st.session_state:
    st.session_state.last_deep = ""

def clear_text():
    st.session_state["main_input"] = ""
    st.session_state.last_groq = ""
    st.session_state.last_deep = ""

# ================== 5. UI TEXT ==================
UI_TEXT = {
    "vi_to_jp": {
        "title": "LSA TRANSLATOR", "subtitle": "Powered by Groq ⚡ & DeepSeek 🐳",
        "placeholder": "Nhập nội dung cần dịch vào đây... (Ctrl + Enter để dịch)",
        "button": "🌊 Dịch Tốc Độ Cao", "toast": "Đã dịch xong cả 2 mô hình!",
        "label_context": "Ngữ cảnh:", "label_input": "Văn bản nguồn:", "result_title": "BẢN DỊCH",
        "warning": "Vui lòng nhập nội dung cần dịch.", "footer": "© 2026 LinkStoryAsia | Design Team Internal Tool Ver 6.0",
        "lang_left": "Tiếng Việt 🇻🇳", "lang_right": "Tiếng Nhật 🇯🇵",
        "btn_clear": "🗑️", "contexts": ["Văn phòng", "Kính ngữ", "Thân mật"],
        "processing": "Processing...", "btn_copy": "📋"
    },
    "jp_to_vi": {
        "title": "LSA TRANSLATOR", "subtitle": "Powered by Groq ⚡ & DeepSeek 🐳",
        "placeholder": "翻訳する内容を入力してください... (Ctrl + Enter)",
        "button": "🌊 超高速翻訳", "toast": "翻訳が完了しました！",
        "label_context": "文脈:", "label_input": "原文:", "result_title": "BẢN DỊCH",
        "warning": "内容を入力してください。", "footer": "© 2026 LinkStoryAsia | デザインチーム翻訳ツール Ver 6.0",
        "lang_left": "日本語 🇯🇵", "lang_right": "ベトナム語 🇻🇳",
        "btn_clear": "🗑️", "contexts": ["ビジネス", "丁寧語", "カジュアル"],
        "processing": "翻訳中...", "btn_copy": "📋"
    }
}

current_lang_key = "jp_to_vi" if st.session_state.is_jp_to_vi else "vi_to_jp"
ui = UI_TEXT[current_lang_key]

# ================== SIDEBAR ==================
with st.sidebar:
    st.markdown("### 📜 Lịch sử dịch gần đây")
    if st.session_state.history:
        for item in reversed(st.session_state.history[-5:]):
            preview = (item['source'][:48] + "...") if len(item['source']) > 48 else item['source']
            with st.expander(f"🕒 {item['time']} • {preview}", expanded=False):
                st.caption(item['source'][:120] + "..." if len(item['source']) > 120 else item['source'])
    else:
        st.caption("Chưa có bản dịch nào.")

# ================== 6. SYSTEM PROMPT ==================
if st.session_state.is_jp_to_vi:
    sys_msg = f"""You are an expert Japanese to Vietnamese translator for a Manga Retouching and Graphic Design team.
Your task is to translate work instructions from Japanese clients into accurate, actionable, and natural Vietnamese for professional retouchers.

[CRITICAL PROJECT RULES - MUST FOLLOW]
1. FOLDER VS LAYER: "Inpainting" MUST ALWAYS be translated and understood as a Folder (Group / Nhóm / Thư mục). NEVER translate it as a single Layer, even if the Japanese input incorrectly says "Inpaintingレイヤー". Translate it as "Folder Inpainting".
2. NAMING CONVENTIONS: Always standardize date formats in folder/file names to YYYY/MM/DD (e.g., 2026/31/03 -> 2026/03/31). Do not translate specific nouns like "LS" or "Vinh".
3. NO LITERAL TRANSLATION: Understand the context of Photoshop actions.
4. ONLY RETURN TRANSLATION: Do not explain, do not say hello, do not add prefixes.

[MANDATORY GLOSSARY - EXACT MATCH REQUIRED]
# Text & Art Elements:
- フキダシ (Fukidashi) -> Bóng thoại
- 描き文字 (Kakimoji) -> Chữ hiệu ứng (SFX) / Chữ vẽ tay
- 描き足し / 加筆 (Kakitashi / Kahitsu) -> Vẽ bù / Redraw
- 背景にかかっている (Haikei ni kakatteiru) -> Đè lên phông nền / Lấn vào nền
- 白抜き (Shironuki) -> Viền trắng / Chữ đục lủng nền
- ベタ / ベタ塗り (Beta / Betanuri) -> Mảng đen / Tô đen (Solid fill)
- トーン削り (Toon kezuri) -> Cạo tone / Xóa mờ tone
- 断ち切り (Tachikiri) -> Tràn lề (Bleed)
- 単行本 (Tankoubon) -> Truyện dài / Tankoubon
- 読切 (Yomikiri) -> Truyện ngắn / Yomikiri

# Photoshop & Technical Terms:
- レイヤーセット / フォルダ (Reiyaa setto / Foruda) -> Folder / Group
- 統合する (Tougou suru) -> Gộp layer / Merge
- モアレ (Moare) -> Lỗi Moire / Lỗi rạn hạt tone
- ジャギー (Jagii) -> Răng cưa
- アンチエイリアス (Anchieiriasu) -> Khử răng cưa (Anti-alias)
- ガウスぼかし (Gausu bokashi) -> Làm mờ (Gaussian Blur)
{dict_prompt_str}

[EXAMPLES FOR CONTEXT]
Example 1:
Input: フキダシの中の日本語テキストは全て消去し、背景にかかっている描き文字はそのまま残してください。
Output: Xóa toàn bộ text tiếng Nhật bên trong bóng thoại, và giữ nguyên các chữ hiệu ứng (SFX) đè lên phông nền.

Example 2:
Input: 修正後の背景や描き足し部分はInpaintingレイヤーに結合して、2026/31/03_レタッチ_LS_Vinhに保存してください。
Output: Phông nền sau khi chỉnh sửa và phần vẽ bù (redraw) hãy gộp vào Folder Inpainting, và lưu vào folder 2026/03/31_レタッチ_LS_Vinh.
"""
else:
    sys_msg = f"""Bạn là một chuyên gia dịch thuật tiếng Việt sang tiếng Nhật, làm việc tại bộ phận Design, Manga, Webtoon.
Đặc thù văn bản: Bao gồm thuật ngữ kỹ thuật (Photoshop) VÀ giao tiếp văn phòng, chỉ thị công việc hàng ngày.

[NHIỆM VỤ TỐI THƯỢNG]
Chỉ trả về bản dịch cuối cùng. Tuyệt đối KHÔNG giải thích, KHÔNG chào hỏi, KHÔNG thêm tiền tố như 'Bản dịch:'.

[QUY TẮC DỊCH THUẬT & NGỮ CẢNH]
1. Tự nhiên theo giao tiếp Nhật Bản: Chuyển đổi linh hoạt văn phong.
2. Tên riêng của người/Dự án (VD: LS, Vinh): TUYỆT ĐỐI GIỮ NGUYÊN không phiên âm.
3. Từ điển thuật ngữ BẮT BUỘC:
   - Retouch -> レタッチ
   - Vẽ bù / Vẽ thêm -> 描き込み / 加筆する
   - Lettering -> 写植
   - Làm sạch -> ゴミ取り
   - Layer ẩn -> 非表示レイヤー
   - Folder / Group -> フォルダ / グループ
   - Inpainting -> インペイント
   - Script -> スクリプト
   - Chữ hiệu ứng (SFX) -> 描き文字
   - Viền trắng / Đục lủng nền -> 白抜き
   - Tô đen / Solid fill -> ベタ塗り
   - Cạo tone -> トーン削り
   - Tràn lề -> 断ち切り
   - Truyện dài / tankoubon -> 単行本
   - Truyện ngắn / yomikiri -> 読切
4. Ghép cặp thuật ngữ: Định dạng 'Tiếng Nhật (Tiếng Anh)'.
5. Văn phong: Chuyên nghiệp, chuẩn xác."""

# ================== 7. HIỂN THỊ GIAO DIỆN CHÍNH ==================
st.markdown(
    f'<div class="groq-title-container">'
    f'<div class="groq-title">{ui["title"]}</div>'
    f'<div class="groq-subtitle">{ui["subtitle"]}</div>'
    f'</div>',
    unsafe_allow_html=True
)

col_l, col_btn, col_r = st.columns([2, 1, 2])
with col_l:
    st.markdown(f"<h4 style='text-align: right; color: #a0a0a0;'>{ui['lang_left']}</h4>", unsafe_allow_html=True)
with col_btn:
    if st.button("⇄", use_container_width=True, help="Đảo chiều dịch"):
        st.session_state.is_jp_to_vi = not st.session_state.is_jp_to_vi
        st.session_state.last_groq = ""
        st.session_state.last_deep = ""
        st.rerun()
with col_r:
    st.markdown(f"<h4 style='text-align: left; color: #00b4ff;'>{ui['lang_right']}</h4>", unsafe_allow_html=True)

st.write("")

col_spacer1, col_clear = st.columns([8, 1])
with col_clear:
    st.button(ui["btn_clear"], on_click=clear_text, use_container_width=True)

with st.form(key='translation_form', clear_on_submit=False):
    source_text = st.text_area(
        ui["label_input"], height=160,
        placeholder=ui["placeholder"],
        key="main_input",
        label_visibility="collapsed"
    )
    col1, col2 = st.columns([2, 1])
    with col1:
        mode = st.selectbox(ui["label_context"], ui["contexts"], label_visibility="collapsed")
    with col2:
        submit_button = st.form_submit_button(ui["button"], use_container_width=True)

# ================== 8. XỬ LÝ DỊCH ==================
if submit_button and source_text.strip():
    st.markdown(
        '<div class="result-header"><span style="font-size: 22px;">🌊</span> KẾT QUẢ DỊCH</div>',
        unsafe_allow_html=True
    )

    col_groq, col_deep = st.columns(2)
    groq_stream_placeholder = col_groq.empty()
    deep_stream_placeholder = col_deep.empty()

    loading_placeholder = st.empty()
    with loading_placeholder:
        st.info("⚡ Đang dịch bằng Groq và 🐳 DeepSeek...")

    try:
        target_lang = "Vietnamese" if st.session_state.is_jp_to_vi else "Japanese"
        prompt = f"Translate the following text into {target_lang} (Context/Style: {mode}):\n\n{source_text}"

        # ── Groq: stream vào markdown tạm, sau đó render result box ──
        groq_text = ""
        groq_stream_placeholder.markdown("⚡ **Groq** — Đang dịch...")
        for chunk in groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "system", "content": sys_msg}, {"role": "user", "content": prompt}],
            temperature=0.0,
            stream=True
        ):
            content = chunk.choices[0].delta.content or ""
            groq_text += content
            # Hiển thị streaming tạm bằng markdown (không có copy button)
            groq_stream_placeholder.markdown(
                f"⚡ **Groq**\n\n{groq_text}",
            )

        # Render result box thật sự bên trong components.html (có copy hoạt động)
        render_result_box(groq_stream_placeholder, "⚡ Groq", groq_text)

        # ── DeepSeek: tương tự ──
        deep_text = ""
        deep_stream_placeholder.markdown("🐳 **DeepSeek** — Đang dịch...")
        for chunk in deepseek_client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[{"role": "system", "content": sys_msg}, {"role": "user", "content": prompt}],
            temperature=0.0,
            stream=True
        ):
            content = chunk.choices[0].delta.content or ""
            deep_text += content
            deep_stream_placeholder.markdown(
                f"🐳 **DeepSeek**\n\n{deep_text}",
            )

        render_result_box(deep_stream_placeholder, "🐳 DeepSeek", deep_text)

        loading_placeholder.empty()

        # Lưu vào session để re-render nếu cần
        st.session_state.last_groq = groq_text
        st.session_state.last_deep = deep_text

        # Lưu lịch sử
        tz_vn = timezone(timedelta(hours=7))
        st.session_state.history.append({
            "time": datetime.now(tz_vn).strftime("%H:%M"),
            "source": source_text,
            "result": groq_text + "\n\n" + deep_text,
            "mode": mode
        })

        st.toast("✅ Dịch xong cả 2 mô hình!", icon="🌊")

    except Exception as e:
        loading_placeholder.empty()
        st.error(f"Lỗi hệ thống: {str(e)}")

elif submit_button:
    st.warning(ui["warning"])

# ── Hiển thị lại kết quả lần dịch trước (nếu có, tránh mất khi tương tác UI) ──
elif st.session_state.last_groq and st.session_state.last_deep:
    st.markdown(
        '<div class="result-header"><span style="font-size: 22px;">🌊</span> KẾT QUẢ DỊCH</div>',
        unsafe_allow_html=True
    )
    col_groq2, col_deep2 = st.columns(2)
    with col_groq2:
        groq_ph = st.empty()
        render_result_box(groq_ph, "⚡ Groq", st.session_state.last_groq)
    with col_deep2:
        deep_ph = st.empty()
        render_result_box(deep_ph, "🐳 DeepSeek", st.session_state.last_deep)

st.markdown(
    f'<div style="text-align: center; color: #555; font-size: 12px; margin-top: 50px; font-weight: 500;">{ui["footer"]}</div>',
    unsafe_allow_html=True
)
