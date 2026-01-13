from db import get_users

def match_users(vacancy_tags: list[str]) -> list[int]:
    matched = []

    for user_id, tags in get_users():
        user_tags = tags.split(",")

        if set(vacancy_tags).intersection(user_tags):
            matched.append(user_id)

    return matched
