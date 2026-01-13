import re

PROFESSIONS = {
    "python": ["python", "django", "flask", "fastapi"],
    "designer": ["design", "figma", "ux", "ui"],
    "manager": ["manager", "pm", "product", "project"],
    "frontend": ["react", "vue", "javascript"],
    "backend": ["backend", "api", "sql"]
}

LEVELS = {
    "junior": ["junior", "джуниор"],
    "middle": ["middle", "мидл"],
    "senior": ["senior", "сеньор", "lead"]
}

def extract_tags(text: str) -> dict:
    t = text.lower()

    profession = "unknown"
    for key, words in PROFESSIONS.items():
        if any(w in t for w in words):
            profession = key
            break

    level = "not specified"
    for lvl, words in LEVELS.items():
        if any(w in t for w in words):
            level = lvl
            break

    if "удал" in t or "remote" in t:
        format_ = "remote"
    elif "офис" in t:
        format_ = "office"
    else:
        format_ = "not specified"

    skills = re.findall(r"\b(python|django|fastapi|sql|react|figma|docker|linux)\b", t)
    salary = re.search(r"(\d{2,3}\s?000)", t)

    return {
        "profession": profession,
        "level": level,
        "format": format_,
        "skills": list(set(skills)),
        "salary": salary.group(1) if salary else "not specified"
    }
