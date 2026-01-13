import re

PROFESSIONS = {
    "python": ["python", "django", "flask"],
    "frontend": ["javascript", "react", "vue"],
    "designer": ["figma", "ui", "ux"],
    "manager": ["project", "pm", "product"]
}

LEVELS = {
    "junior": ["junior", "начальный", "стажер"],
    "middle": ["middle"],
    "senior": ["senior", "lead"]
}

FORMATS = {
    "remote": ["remote", "удаленно", "удалённо"],
    "office": ["офис"],
    "hybrid": ["гибрид"]
}


def extract_tags(text: str) -> dict:
    text = text.lower()

    def find(map_):
        for k, words in map_.items():
            if any(w in text for w in words):
                return k
        return "unknown"

    skills = re.findall(r"\b(python|django|sql|react|figma)\b", text)

    return {
        "profession": find(PROFESSIONS),
        "level": find(LEVELS),
        "format": find(FORMATS),
        "skills": list(set(skills))
    }
