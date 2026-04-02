from openai import OpenAI

from app.agent import Agent
from app.parser import PDFParser
from app.compiler import LatexCompiler
from app.config import AppConfig


class PresentationPipeline:
    def __init__(self, config: AppConfig):
        self.config = config
        self.client = OpenAI(
            api_key=config.api_key,
            base_url=config.base_url,
            timeout=config.timeout
        )

        self.parser = PDFParser(max_chars=config.max_pdf_chars)
        self.compiler = LatexCompiler()

        # 3 个 agent 都由同一个 Agent 类实例化
        self.extract_agent = Agent(
            name="Agent 1 提炼内容",
            system_prompt=(
                "你是一个学术专家。请提炼这篇论文的："
                "1.背景 2.核心方法 3.结论。"
                "只提取最核心骨架，越短越好。"
            ),
            client=self.client,
            model=config.model,
        )

        self.bullet_agent = Agent(
            name="Agent 2 生成演讲要点",
            system_prompt="""
你是一个极简主义的 PPT 专家。请将内容压缩为 Bullet Points。
【死命令】：
1. 整体只能有 3 到 4 个部分。
2. 每个部分下最多 3 条要点。
3. 每条要点不超过 15 个字。
""".strip(),
            client=self.client,
            model=config.model,
        )

        self.latex_agent = Agent(
            name="Agent 3 生成 LaTeX 排版",
            system_prompt=r"""
你是一个排版严谨的 LaTeX 专家。
【严格纪律】：
1. 必须使用 \usepackage{ctex}。
2. 严格生成 4 到 5 个 frame（1页标题 + 3到4页内容），绝不能超过 5 页。
3. 绝对禁止使用任何图片！不要出现 \includegraphics，也不要画占位框。只能有纯文本和 itemize 列表。
4. 只输出 LaTeX 代码，不加任何解释。
""".strip(),
            client=self.client,
            model=config.model,
        )

    def run(self, pdf_path: str, tex_output_path: str = "presentation.tex", compile_pdf: bool = True) -> None:
        raw_text = self.parser.extract_content(pdf_path)
        if not raw_text:
            print("❌ 未能提取到 PDF 内容，流程终止。")
            return

        extracted_info = self.extract_agent.run(raw_text)
        bullets = self.bullet_agent.run(extracted_info)
        latex_code = self.latex_agent.run(bullets)

        clean_latex = self.compiler.clean_latex_output(latex_code)
        self.compiler.save_tex(tex_output_path, clean_latex)

        if compile_pdf:
            self.compiler.compile(tex_output_path)