import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    bot_token: str
    admin_chat_id: int
    rate_amd_per_star: float
    min_stars: int
    max_stars: int
    card_number: str


def load_config() -> Config:
    return Config(
        bot_token=os.getenv("BOT_TOKEN", ""),
        admin_chat_id=int(os.getenv("ADMIN_CHAT_ID", "0")),
        rate_amd_per_star=float(os.getenv("RATE_AMD_PER_STAR", "6.5")),
        min_stars=int(os.getenv("MIN_STARS", "50")),
        max_stars=int(os.getenv("MAX_STARS", "100000")),
        card_number=os.getenv("CARD_NUMBER", ""),
    )
