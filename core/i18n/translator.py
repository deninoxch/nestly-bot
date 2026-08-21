import json
from pathlib import Path
from functools import lru_cache

from core.enums import Language

LOCALES_DIR = Path(__file__).parent / 'locales'

@lru_cache
def _load_locale(lang: str) -> dict:
    file_path = LOCALES_DIR / f'{lang}.json'
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_text(key: str, lang: Language | str = Language.RU) -> str:
    lang_code = lang.value if isinstance(lang, Language) else lang
    locale = _load_locale(lang_code)

    if key not in locale:

        fallback = _load_locale(Language.RU.value)
        return fallback.get(key, f'[[{key}]]')

    return locale[key]
