import os  # 新增：用于读取系统变量
import fitz  # PyMuPDF
from openai import OpenAI
import subprocess
from dotenv import load_dotenv  # 新增：加载 .env 的工具

# --- 0. 加载配置 ---
load_dotenv()  # 这一行会读取同目录下的 .env 文件

# --- 1. 配置部分 ---
# 使用 os.getenv 安全获取 Key，如果找不到会报错提醒
api_key = os.getenv("DEEPSEEK_API_KEY")

client = OpenAI(
    api_key=api_key, 
    base_url="https://api.deepseek.com",
    timeout=60.0 
)

# --- 2. 解析模块 ---
def extract_content_from_pdf(pdf_path):
    print(f"📖 正在扫描论文: {pdf_path}...")
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        return text.replace('\n', ' ').strip()[:5000] 
    except Exception as e:
        print(f"❌ PDF 读取失败: {e}")
        return None

# --- 3. Agent 核心逻辑 (保持不变) ---
def agent_1_extract(text):
    print("--- Agent 1 正在提炼内容... ---")
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "你是一个学术专家。请提炼这篇论文的：1.背景 2.核心方法 3.结论。只提取最核心骨架，越短越好。"},
            {"role": "user", "content": text}
        ]
    )
    return response.choices[0].message.content

def agent_2_to_bullets(extracted_info):
    print("--- Agent 2 正在生成演讲要点... ---")
    system_prompt = """
    你是一个极简主义的 PPT 专家。请将内容压缩为 Bullet Points。
    【死命令】：
    1. 整体只能有 3 到 4 个部分。
    2. 每个部分下最多 3 条要点。
    3. 每条要点不超过 15 个字。
    """
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": extracted_info}
        ]
    )
    return response.choices[0].message.content

def agent_3_to_latex(bullets):
    print("--- Agent 3 正在生成 LaTeX 排版... ---")
    system_prompt = """
    你是一个排版严谨的 LaTeX 专家。
    【严格纪律】：
    1. 必须使用 \\usepackage{ctex}。
    2. 严格生成 4 到 5 个 frame（1页标题 + 3到4页内容），绝不能超过 5 页。
    3. 绝对禁止使用任何图片！不要出现 \\includegraphics，也不要画占位框。只能有纯文本和 itemize 列表。
    4. 只输出 LaTeX 代码，不加任何解释。
    """
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": bullets}
        ]
    )
    return response.choices[0].message.content

# --- 4. 主运行逻辑 ---
if __name__ == "__main__":
    pdf_filename = "test.pdf" 
    
    raw_text = extract_content_from_pdf(pdf_filename)
    
    if raw_text:
        info = agent_1_extract(raw_text)
        ppt_content = agent_2_to_bullets(info)
        latex_code = agent_3_to_latex(ppt_content)
        
        # 清洗 AI 输出的 Markdown 标记
        clean_latex = latex_code.replace("```latex\n", "").replace("```", "").strip()
    
        with open("presentation.tex", "w", encoding="utf-8") as f:
            f.write(clean_latex)
        print("\n✅ 已生成干净的 presentation.tex 代码！")
        print("🚀 正在调用本地编译器，静默生成 PDF 中，请稍候...")
        
        subprocess.run(["xelatex", "-interaction=nonstopmode", "presentation.tex"])
        print("\n🎉 编译结束！快去看看文件夹里的 presentation.pdf 吧！")