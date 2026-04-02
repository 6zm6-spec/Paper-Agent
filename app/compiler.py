import subprocess


class LatexCompiler:
    @staticmethod
    def clean_latex_output(latex_text: str) -> str:
        return (
            latex_text
            .replace("```latex", "")
            .replace("```tex", "")
            .replace("```", "")
            .strip()
        )

    @staticmethod
    def save_tex(tex_path: str, latex_text: str) -> None:
        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(latex_text)
        print(f"✅ 已写入 {tex_path}")

    @staticmethod
    def compile(tex_path: str) -> None:
        print("🚀 正在调用本地编译器，静默生成 PDF 中，请稍候...")
        result = subprocess.run(
            ["xelatex", "-interaction=nonstopmode", tex_path],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print("🎉 编译结束！请查看生成的 PDF。")
        else:
            print("❌ LaTeX 编译失败。下面是错误信息：")
            print(result.stdout)
            print(result.stderr)