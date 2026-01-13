import re

PROFESSIONS = {
    "python": ["python", "django", "flask"],
    "designer": ["design", "figma", "ui", "ux"],
    "manager": ["manager", "pm", "product"]
}

LEVELS = {
    "junior": ["junior", "стажер"],
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

    def find(mapping):
        for key, words in mapping.items():
            if any(w in text for w in words):
                return key
        return "unknown"

    skills = re.findall(r"\b(python|django|sql|react|figma)\b", text)

    return {
        "profession": find(PROFESSIONS),
        "level": find(LEVELS),
        "format": find(FORMATS),
        "skills": list(set(skills))
    }
