import os
import uvicorn
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# 引入你写好的核心组件
from app.config import load_config
from app.pipeline import PresentationPipeline

# 1. 初始化 FastAPI 应用
app = FastAPI(
    title="Paper2Slides API",
    description="自动将学术论文 PDF 转换为 Beamer 幻灯片的后端服务",
    version="1.0.0"
)

# 可选：解决跨域问题（方便前端联调）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化你的流水线
try:
    config = load_config()
    pipeline = PresentationPipeline(config=config)
    print("✅ 系统配置与流水线加载成功！")
except Exception as e:
    print(f"❌ 系统初始化失败: {e}")
    pipeline = None

# 2. 定义处理 PDF 的核心接口
@app.post("/generate-ppt", summary="上传 PDF，生成 PPT")
async def generate_ppt(file: UploadFile = File(...)):
    if pipeline is None:
        return JSONResponse(status_code=500, content={"error": "服务器未正确初始化，请检查 API Key。"})
        
    if not file.filename.endswith('.pdf'):
        return JSONResponse(status_code=400, content={"error": "请上传 PDF 格式的文件！"})

    print(f"📥 [Server] 接收到文件: {file.filename}")
    
    # 构建临时文件名和输出文件名
    temp_pdf_path = f"temp_upload_{file.filename}"
    tex_output_path = "presentation.tex"
    pdf_output_path = "presentation.pdf"

    try:
        # 将前端传来的文件暂存到本地
        with open(temp_pdf_path, "wb") as f:
            f.write(await file.read())
            
        print("🚀 [Server] 触发流水线...")
        
        # 调用你的业务代码！
        pipeline.run(
            pdf_path=temp_pdf_path,
            tex_output_path=tex_output_path,
            compile_pdf=True
        )
        
        # 完事后把临时 PDF 删掉，保持服务器干净
        if os.path.exists(temp_pdf_path):
            os.remove(temp_pdf_path)
        
        # 检查是否成功生成了 PDF
        if os.path.exists(pdf_output_path):
            print("✅ [Server] 准备向前端返回生成的 PDF 文件...")
            return FileResponse(
                path=pdf_output_path, 
                filename=f"Slides_{file.filename}", 
                media_type="application/pdf"
            )
        else:
            return JSONResponse(status_code=500, content={"error": "LaTeX 编译失败，未生成 PDF。请检查终端的报错信息。"})
            
    except Exception as e:
        # 确保出错了也会清理临时文件
        if os.path.exists(temp_pdf_path):
            os.remove(temp_pdf_path)
        return JSONResponse(status_code=500, content={"error": f"服务器内部错误: {str(e)}"})

# 3. 启动服务器
if __name__ == "__main__":
    print("🌍 正在启动本地 Web 服务器...")
    # host="0.0.0.0" 意味着允许局域网内的其他人访问
    uvicorn.run(app, host="0.0.0.0", port=8000)