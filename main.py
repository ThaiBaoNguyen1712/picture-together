import streamlit as st
from rembg import remove
from PIL import Image, ImageEnhance
import io
import base64
import time

st.set_page_config(page_title="AI Photo Studio Pro", layout="wide")

# --- HÀM HỖ TRỢ ---
def prepare_person(img, scale, sharp):
    """Chuẩn bị ảnh người: điều chỉnh kích thước và độ sắc nét"""
    if img is None: 
        return None
    enhancer = ImageEnhance.Sharpness(img)
    img = enhancer.enhance(sharp)
    nw = int(img.width * (scale / 100))
    nh = int(img.height * (scale / 100))
    return img.resize((nw, nh), Image.Resampling.LANCZOS)

def remove_background_with_progress(image, label):
    """Tách nền với thanh tiến trình"""
    progress_bar = st.progress(0, text=f"🎯 Đang phân tích {label}...")
    time.sleep(0.3)
    
    progress_bar.progress(30, text=f"🤖 AI đang xử lý {label}...")
    img_rgba = Image.open(image).convert("RGBA")
    
    progress_bar.progress(50, text=f"✂️ Đang tách nền {label}...")
    result = remove(img_rgba)
    
    progress_bar.progress(100, text=f"✅ Hoàn thành {label}!")
    time.sleep(0.3)
    progress_bar.empty()
    
    return result

def pil_to_base64(img):
    """Chuyển PIL Image sang base64"""
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

def create_draggable_canvas(bg_img, img_a, img_b, pos_a, pos_b, scale_a, scale_b, order):
    """Tạo canvas có thể kéo thả (hỗ trợ cả chuột và touch)"""
    # Chuẩn bị ảnh
    p_a = prepare_person(img_a, scale_a, 1.5)
    p_b = prepare_person(img_b, scale_b, 1.5)
    
    # Chuyển sang base64
    bg_b64 = pil_to_base64(bg_img)
    a_b64 = pil_to_base64(p_a)
    b_b64 = pil_to_base64(p_b)
    
    html_code = f"""
    <div style="text-align: center; -webkit-user-select: none; user-select: none;">
        <canvas id="canvas" width="{bg_img.width}" height="{bg_img.height}" 
                style="border: 3px solid #4CAF50; border-radius: 10px; cursor: move; max-width: 100%; touch-action: none;"></canvas>
        <div id="instruction" style="margin-top: 10px; color: #666; font-size: 14px;">
            <span id="desktop-hint" style="display: inline;">🖱️ Kéo thả để di chuyển người</span>
            <span id="mobile-hint" style="display: none;">👆 Chạm và kéo để di chuyển người</span>
        </div>
    </div>
    <script>
        // Phát hiện thiết bị di động
        const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) || 
                        ('ontouchstart' in window) || (navigator.maxTouchPoints > 0);
        
        if (isMobile) {{
            document.getElementById('desktop-hint').style.display = 'none';
            document.getElementById('mobile-hint').style.display = 'inline';
        }}
        
        const canvas = document.getElementById('canvas');
        const ctx = canvas.getContext('2d');
        
        // Tải ảnh
        const bgImg = new Image();
        const imgA = new Image();
        const imgB = new Image();
        
        bgImg.src = 'data:image/png;base64,{bg_b64}';
        imgA.src = 'data:image/png;base64,{a_b64}';
        imgB.src = 'data:image/png;base64,{b_b64}';
        
        // Vị trí và kích thước
        let posA = {{ x: {pos_a[0]}, y: {pos_a[1]} }};
        let posB = {{ x: {pos_b[0]}, y: {pos_b[1]} }};
        const sizeA = {{ w: {p_a.width}, h: {p_a.height} }};
        const sizeB = {{ w: {p_b.width}, h: {p_b.height} }};
        const order = "{order}";
        
        let dragging = null;
        let offsetX = 0;
        let offsetY = 0;
        
        function draw() {{
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.drawImage(bgImg, 0, 0);
            
            // Vẽ theo thứ tự lớp
            if (order === "Người A") {{
                ctx.drawImage(imgB, posB.x - sizeB.w/2, posB.y - sizeB.h/2);
                ctx.drawImage(imgA, posA.x - sizeA.w/2, posA.y - sizeA.h/2);
                
                // Viền cho người đang được chọn
                if (dragging === 'B') {{
                    ctx.strokeStyle = '#FF5722';
                    ctx.lineWidth = 4;
                    ctx.setLineDash([10, 5]);
                    ctx.strokeRect(posB.x - sizeB.w/2 - 5, posB.y - sizeB.h/2 - 5, sizeB.w + 10, sizeB.h + 10);
                    ctx.setLineDash([]);
                }}
                if (dragging === 'A') {{
                    ctx.strokeStyle = '#2196F3';
                    ctx.lineWidth = 4;
                    ctx.setLineDash([10, 5]);
                    ctx.strokeRect(posA.x - sizeA.w/2 - 5, posA.y - sizeA.h/2 - 5, sizeA.w + 10, sizeA.h + 10);
                    ctx.setLineDash([]);
                }}
            }} else {{
                ctx.drawImage(imgA, posA.x - sizeA.w/2, posA.y - sizeA.h/2);
                ctx.drawImage(imgB, posB.x - sizeB.w/2, posB.y - sizeB.h/2);
                
                if (dragging === 'A') {{
                    ctx.strokeStyle = '#2196F3';
                    ctx.lineWidth = 4;
                    ctx.setLineDash([10, 5]);
                    ctx.strokeRect(posA.x - sizeA.w/2 - 5, posA.y - sizeA.h/2 - 5, sizeA.w + 10, sizeA.h + 10);
                    ctx.setLineDash([]);
                }}
                if (dragging === 'B') {{
                    ctx.strokeStyle = '#FF5722';
                    ctx.lineWidth = 4;
                    ctx.setLineDash([10, 5]);
                    ctx.strokeRect(posB.x - sizeB.w/2 - 5, posB.y - sizeB.h/2 - 5, sizeB.w + 10, sizeB.h + 10);
                    ctx.setLineDash([]);
                }}
            }}
            
            // Hiển thị tọa độ khi đang kéo
            if (dragging) {{
                ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
                ctx.fillRect(10, 10, 200, 50);
                ctx.fillStyle = 'white';
                ctx.font = '16px Arial';
                const pos = dragging === 'A' ? posA : posB;
                ctx.fillText(`Người ${{dragging}}`, 20, 30);
                ctx.fillText(`X: ${{Math.round(pos.x)}}, Y: ${{Math.round(pos.y)}}`, 20, 50);
            }}
        }}
        
        function isInside(x, y, pos, size) {{
            return x >= pos.x - size.w/2 && x <= pos.x + size.w/2 &&
                   y >= pos.y - size.h/2 && y <= pos.y + size.h/2;
        }}
        
        function getCanvasCoordinates(e) {{
            const rect = canvas.getBoundingClientRect();
            const scaleX = canvas.width / rect.width;
            const scaleY = canvas.height / rect.height;
            
            let clientX, clientY;
            
            if (e.touches && e.touches.length > 0) {{
                clientX = e.touches[0].clientX;
                clientY = e.touches[0].clientY;
            }} else {{
                clientX = e.clientX;
                clientY = e.clientY;
            }}
            
            return {{
                x: (clientX - rect.left) * scaleX,
                y: (clientY - rect.top) * scaleY
            }};
        }}
        
        function handleStart(e) {{
            e.preventDefault();
            const coords = getCanvasCoordinates(e);
            const x = coords.x;
            const y = coords.y;
            
            // Ưu tiên người ở trên cùng
            if (order === "Người A") {{
                if (isInside(x, y, posA, sizeA)) {{
                    dragging = 'A';
                    offsetX = x - posA.x;
                    offsetY = y - posA.y;
                }} else if (isInside(x, y, posB, sizeB)) {{
                    dragging = 'B';
                    offsetX = x - posB.x;
                    offsetY = y - posB.y;
                }}
            }} else {{
                if (isInside(x, y, posB, sizeB)) {{
                    dragging = 'B';
                    offsetX = x - posB.x;
                    offsetY = y - posB.y;
                }} else if (isInside(x, y, posA, sizeA)) {{
                    dragging = 'A';
                    offsetX = x - posA.x;
                    offsetY = y - posA.y;
                }}
            }}
            
            if (dragging) {{
                canvas.style.cursor = 'grabbing';
            }}
            draw();
        }}
        
        function handleMove(e) {{
            if (!dragging) return;
            e.preventDefault();
            
            const coords = getCanvasCoordinates(e);
            const x = coords.x;
            const y = coords.y;
            
            if (dragging === 'A') {{
                posA.x = Math.max(sizeA.w/2, Math.min(canvas.width - sizeA.w/2, x - offsetX));
                posA.y = Math.max(sizeA.h/2, Math.min(canvas.height - sizeA.h/2, y - offsetY));
            }} else if (dragging === 'B') {{
                posB.x = Math.max(sizeB.w/2, Math.min(canvas.width - sizeB.w/2, x - offsetX));
                posB.y = Math.max(sizeB.h/2, Math.min(canvas.height - sizeB.h/2, y - offsetY));
            }}
            draw();
        }}
        
        function handleEnd(e) {{
            if (dragging) {{
                e.preventDefault();
                // Gửi tọa độ về Streamlit
                window.parent.postMessage({{
                    type: 'streamlit:setComponentValue',
                    value: {{
                        posA: posA,
                        posB: posB
                    }}
                }}, '*');
                canvas.style.cursor = 'move';
            }}
            dragging = null;
            draw();
        }}
        
        // Mouse events
        canvas.addEventListener('mousedown', handleStart);
        canvas.addEventListener('mousemove', handleMove);
        canvas.addEventListener('mouseup', handleEnd);
        canvas.addEventListener('mouseleave', handleEnd);
        
        // Touch events cho điện thoại
        canvas.addEventListener('touchstart', handleStart, {{ passive: false }});
        canvas.addEventListener('touchmove', handleMove, {{ passive: false }});
        canvas.addEventListener('touchend', handleEnd, {{ passive: false }});
        canvas.addEventListener('touchcancel', handleEnd, {{ passive: false }});
        
        // Vẽ lần đầu khi ảnh load xong
        let loaded = 0;
        [bgImg, imgA, imgB].forEach(img => {{
            img.onload = () => {{
                loaded++;
                if (loaded === 3) draw();
            }};
        }});
    </script>
    """
    return html_code

# --- KHỞI TẠO SESSION STATE ---
if 'img_a' not in st.session_state: 
    st.session_state.img_a = None
if 'img_b' not in st.session_state: 
    st.session_state.img_b = None
if 'pos_a' not in st.session_state:
    st.session_state.pos_a = None
if 'pos_b' not in st.session_state:
    st.session_state.pos_b = None
if 'processed' not in st.session_state:
    st.session_state.processed = False

# --- HEADER ---
st.title("📸 AI Photo Studio Pro")
st.markdown("*Ghép ảnh chuyên nghiệp - Hỗ trợ cả máy tính và điện thoại*")

# --- SIDEBAR ---
st.sidebar.header("🎨 Tùy chỉnh")

with st.sidebar.expander("⚙️ Cài đặt lớp", expanded=True):
    order = st.selectbox("Người đứng trước", ["Người A", "Người B"], key="order")
    
with st.sidebar.expander("📏 Kích thước", expanded=True):
    scale_a = st.slider("Kích thước Người A (%)", 10, 300, 100, 5, key="scale_a", 
                        help="Điều chỉnh kích thước người A")
    scale_b = st.slider("Kích thước Người B (%)", 10, 300, 100, 5, key="scale_b",
                        help="Điều chỉnh kích thước người B")

with st.sidebar.expander("🔍 Chất lượng", expanded=True):
    sharpness = st.slider("Độ sắc nét", 0.5, 3.0, 1.5, 0.1, key="sharp",
                          help="Tăng độ sắc nét cho ảnh người")

st.sidebar.divider()

col_btn1, col_btn2 = st.sidebar.columns(2)
with col_btn1:
    if st.button("🗑️ Reset", use_container_width=True, help="Xóa tất cả và làm lại"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

with col_btn2:
    if st.button("ℹ️ Hướng dẫn", use_container_width=True):
        st.info("""
        **Cách sử dụng:**
        
        1️⃣ Tải 3 ảnh lên
        2️⃣ Chạy AI tách nền
        3️⃣ Kéo thả để sắp xếp
        4️⃣ Tạo & tải ảnh
        
        **Điện thoại:** Chạm và kéo
        **Máy tính:** Click và kéo
        """)

# --- BƯỚC 1: TẢI ẢNH (Responsive) ---
st.header("📤 Bước 1: Tải ảnh lên")

# Mobile-friendly layout
if st.session_state.get('mobile_view', False):
    # Layout dọc cho mobile
    st.subheader("👤 Người A")
    file_a = st.file_uploader("Chọn ảnh người thứ nhất", type=["jpg", "png", "jpeg"], key="file_a")
    if file_a and not st.session_state.processed:
        st.image(file_a, caption="Ảnh gốc A", use_container_width=True)
    
    st.subheader("👥 Người B")
    file_b = st.file_uploader("Chọn ảnh người thứ hai", type=["jpg", "png", "jpeg"], key="file_b")
    if file_b and not st.session_state.processed:
        st.image(file_b, caption="Ảnh gốc B", use_container_width=True)
    
    st.subheader("🖼️ Ảnh nền")
    file_bg = st.file_uploader("Chọn ảnh nền ghép", type=["jpg", "png", "jpeg"], key="file_bg")
    if file_bg:
        st.image(file_bg, caption="Nền", use_container_width=True)
else:
    # Layout ngang cho desktop
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("👤 Người A")
        file_a = st.file_uploader("Chọn ảnh người thứ nhất", type=["jpg", "png", "jpeg"], key="file_a")
        if file_a and not st.session_state.processed:
            st.image(file_a, caption="Ảnh gốc A", use_container_width=True)
    
    with col2:
        st.subheader("👥 Người B")
        file_b = st.file_uploader("Chọn ảnh người thứ hai", type=["jpg", "png", "jpeg"], key="file_b")
        if file_b and not st.session_state.processed:
            st.image(file_b, caption="Ảnh gốc B", use_container_width=True)
    
    with col3:
        st.subheader("🖼️ Ảnh nền")
        file_bg = st.file_uploader("Chọn ảnh nền ghép", type=["jpg", "png", "jpeg"], key="file_bg")
        if file_bg:
            st.image(file_bg, caption="Nền", use_container_width=True)

# --- BƯỚC 2: TÁCH NỀN ---
st.header("🪄 Bước 2: Tách nền bằng AI")

process_btn = st.button("🚀 Chạy AI tách nền", type="primary", disabled=not (file_a and file_b))

if process_btn:
    if file_a and file_b:
        try:
            with st.spinner("⏳ Đang khởi động AI..."):
                st.session_state.img_a = remove_background_with_progress(file_a, "Người A")
                st.session_state.img_b = remove_background_with_progress(file_b, "Người B")
                st.session_state.processed = True
                st.balloons()
                st.success("🎉 Tách nền thành công! Kéo xuống để kéo thả.")
        except Exception as e:
            st.error(f"❌ Lỗi: {str(e)}")
    else:
        st.error("⚠️ Vui lòng tải đủ ảnh!")

# Hiển thị preview ảnh đã tách nền
if st.session_state.img_a and st.session_state.img_b:
    with st.expander("👁️ Xem ảnh đã tách nền"):
        preview_col1, preview_col2 = st.columns(2)
        with preview_col1:
            st.image(st.session_state.img_a, caption="✂️ Người A", use_container_width=True)
        with preview_col2:
            st.image(st.session_state.img_b, caption="✂️ Người B", use_container_width=True)

# --- BƯỚC 3: KÉO THẢ ---
if st.session_state.img_a and st.session_state.img_b and file_bg:
    st.header("🖱️ Bước 3: Kéo thả để sắp xếp")
    
    # Hướng dẫn responsive
    st.info("💡 **Kéo thả** người trên ảnh để di chuyển. Khung màu xuất hiện khi chọn.")
    
    bg_img = Image.open(file_bg).convert("RGBA")
    
    # Khởi tạo vị trí mặc định
    if st.session_state.pos_a is None:
        st.session_state.pos_a = (bg_img.width // 3, bg_img.height // 2)
    if st.session_state.pos_b is None:
        st.session_state.pos_b = (int(bg_img.width // 1.5), bg_img.height // 2)
    
    # Hiển thị canvas kéo thả
    html = create_draggable_canvas(
        bg_img, 
        st.session_state.img_a,
        st.session_state.img_b,
        st.session_state.pos_a,
        st.session_state.pos_b,
        scale_a,
        scale_b,
        order
    )
    
    # Chiều cao responsive
    canvas_height = min(bg_img.height + 100, 800)
    st.components.v1.html(html, height=canvas_height, scrolling=False)
    
    # --- BƯỚC 4: XUẤT KẾT QUẢ ---
    st.header("💾 Bước 4: Lưu kết quả")
    
    if st.button("🎨 Tạo ảnh chất lượng cao", type="primary"):
        with st.spinner("🎨 Đang tạo ảnh chất lượng cao..."):
            progress_compose = st.progress(0)
            
            progress_compose.progress(25, text="Đang chuẩn bị Người A...")
            p_a = prepare_person(st.session_state.img_a, scale_a, sharpness)
            
            progress_compose.progress(50, text="Đang chuẩn bị Người B...")
            p_b = prepare_person(st.session_state.img_b, scale_b, sharpness)
            
            progress_compose.progress(75, text="Đang ghép ảnh...")
            final_img = bg_img.copy()
            
            c_a = (st.session_state.pos_a[0] - p_a.width // 2, st.session_state.pos_a[1] - p_a.height // 2)
            c_b = (st.session_state.pos_b[0] - p_b.width // 2, st.session_state.pos_b[1] - p_b.height // 2)
            
            if order == "Người A":
                final_img.paste(p_b, c_b, p_b)
                final_img.paste(p_a, c_a, p_a)
            else:
                final_img.paste(p_a, c_a, p_a)
                final_img.paste(p_b, c_b, p_b)
            
            progress_compose.progress(100, text="Hoàn thành!")
            time.sleep(0.3)
            progress_compose.empty()
            
            st.image(final_img.convert("RGB"), caption="🎨 Ảnh ghép hoàn thành", use_container_width=True)
            
            # Nút tải xuống
            buf = io.BytesIO()
            final_img.convert("RGB").save(buf, format="JPEG", quality=95)
            buf.seek(0)
            
            st.download_button(
                label="📥 Tải ảnh kết quả (JPEG 95%)",
                data=buf.getvalue(),
                file_name="ai_photo_studio_result.jpg",
                mime="image/jpeg",
                type="primary"
            )

# --- FOOTER ---
st.divider()
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    <p><b>✨ AI Photo Studio Pro</b></p>
    <p>📱 Hỗ trợ: Máy tính, Tablet, Điện thoại</p>
    <p>🎨 Powered by RemBG AI & Streamlit</p>
</div>
""", unsafe_allow_html=True)