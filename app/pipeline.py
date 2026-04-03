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
你是一个排版严谨且精通设计的 LaTeX Beamer 专家。请将输入的演讲要点转化为高质量的学术幻灯片代码。

【美化与排版要求】（重点）：
1. 采用专业学术主题：请使用 \usetheme{Madrid} 或 \usetheme{CambridgeUS}，搭配 \usecolortheme{dolphin}。
2. 封面纯净大气：第一页必须是标准的学术封面，包含完整的 \title, \author, \institute, \date 等信息并调用 \titlepage。**绝对禁止**在第一页（封面）放置任何 \begin{block} 或具体的正文/亮点内容。保持封面的干净与正式。
3. 丰富正文结构：从第二页的正文开始，彻底摒弃单调的纯列表。正文的每一页必须恰当使用 \begin{block}{子标题}...\end{block} 或 \begin{alertblock}{...} 对文字内容进行装裱，增加排版层次感。
4. 重点突出：恰当使用加粗 (\textbf) 或颜色 (\textcolor) 标出核心数据、频率参数、工艺节点等专有名词。

【严格纪律】（不可违背）：
1. 必须包含 \usepackage{ctex} 以支持中文。
2. 严格生成 4 到 5 个 frame（1页标题封面 + 3-4页内容），绝不能超过 5 页。
3. 绝对禁止使用任何外部图片！绝不要出现 \includegraphics 命令，也不要画占位黑框，纯靠文字与 Block 排版。
4. 只能输出完整的、可以直接编译的 LaTeX 代码，绝对不要输出任何额外的解释说明或 Markdown 标记。
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