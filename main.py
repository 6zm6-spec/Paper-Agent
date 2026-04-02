from app.config import load_config
from app.pipeline import PresentationPipeline


def main():
    pdf_filename = "test.pdf"

    config = load_config()
    pipeline = PresentationPipeline(config)
    pipeline.run(pdf_path=pdf_filename, tex_output_path="presentation.tex", compile_pdf=True)


if __name__ == "__main__":
    main()