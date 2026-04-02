import os
from dataclasses import dataclass
from dotenv import load_dotenv


@dataclass
class AppConfig:
    api_key: str
    base_url: str = "https://api.deepseek.com"
    model: str = "deepseek-chat"
    timeout: float = 60.0
    max_pdf_chars: int = 5000


def load_config() -> AppConfig:
    load_dotenv()

    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise ValueError("未检测到 DEEPSEEK_API_KEY，请检查 .env 文件或系统环境变量。")

    return AppConfig(api_key=api_key)