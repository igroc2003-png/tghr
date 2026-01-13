import re

def extract_tags(text: str) -> list[str]:
    """
    Извлекает теги вида #офис #без_опыта #80_120
    """
    if not text:
        return []

    tags = re.findall(r"#([\w\d_]+)", text.lower())
    return tags
