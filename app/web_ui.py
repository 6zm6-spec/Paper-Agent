import streamlit as st
import os

# --- 从你完美封装的模块中引入核心功能 ---
from app.config import load_config
from app.pipeline import PresentationPipeline

# ==========================================
# 1. 网页基础设置
# ==========================================
st.set_page_config(page_title="AI 文献汇报助手", page_icon="📄", layout="centered")
st.title("📄 AI 文献汇报自动化生成器")
st.markdown("上传一篇 PDF 论文，系统将自动提炼核心创新点，并一键生成排版精美的学术汇报 PPT。")
st.divider()

# ==========================================
# 2. 系统初始化 (利用 Streamlit 的缓存机制优化性能)
# ==========================================
@st.cache_resource
def init_pipeline():
    """只在服务启动时加载一次配置和模型，防止每次点击按钮都重新初始化"""
    try:
        config = load_config()
        return PresentationPipeline(config=config), None
    except Exception as e:
        return None, str(e)

pipeline, error_msg = init_pipeline()

if error_msg:
    st.error(f"❌ 系统初始化失败，请检查 .env 文件中的 API Key: {error_msg}")
    st.stop() # 如果没有 Key，直接停止网页后续渲染

# ==========================================
# 3. 核心交互界面
# ==========================================
uploaded_file = st.file_uploader("📂 请在此拖入或上传 PDF 格式的论文", type="pdf")

if uploaded_file is not None:
    st.info(f"已读取文件: {uploaded_file.name}，准备就绪！")
    
    if st.button("🚀 一键生成汇报 PPT", use_container_width=True):
        
        # 准备文件路径
        temp_pdf_path = f"temp_{uploaded_file.name}"
        tex_path = "presentation.tex"
        pdf_path = "presentation.pdf"

        # 运行前清理可能遗留的旧 PDF，防止拿旧文件忽悠人
        if os.path.exists(pdf_path):
            os.remove(pdf_path)

        try:
            # 第一步：把前端传来的文件暂存到服务器本地
            with open(temp_pdf_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            # 第二步：开启动画进度条，呼叫你的 pipeline！
            with st.status("正在执行全自动流水线，请稍候...", expanded=True) as status:
                st.write("🔍 正在扫描论文并调用大模型提取框架...")
                st.write("⚙️ 正在生成底层的 LaTeX 排版代码...")
                st.write("🖨️ 正在调用本地 xelatex 引擎渲染幻灯片...")
                
                # 直接调用封装好的 run() 方法！
                pipeline.run(pdf_path=temp_pdf_path, tex_output_path=tex_path, compile_pdf=True)
                
                status.update(label="✅ 生成流水线执行完毕！", state="complete", expanded=False)

            # 第三步：检查最终的 PDF 有没有顺利产出
            if os.path.exists(pdf_path):
                st.balloons() # 放个庆祝气球特效
                st.success("排版成功！请点击下方按钮下载您的汇报 PPT。")
                
                with open(pdf_path, "rb") as f:
                    st.download_button(
                        label="📥 下载最终版 PPT (PDF格式)",
                        data=f,
                        file_name=f"Slides_{uploaded_file.name}",
                        mime="application/pdf",
                        type="primary"
                    )
            else:
                st.error("❌ 抱歉，LaTeX 编译失败，未生成 PDF。请检查 VS Code 终端里的报错日志。")

        except Exception as e:
            st.error(f"运行过程中发生未知错误: {str(e)}")

        finally:
            # 无论成功还是失败，最后都要把那个临时上传的 PDF 删掉，保持项目整洁
            if os.path.exists(temp_pdf_path):
                os.remove(temp_pdf_path)