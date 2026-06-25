"""Системные промпты и сборка сообщений для GigaChat."""

import json

ROLE_LABELS = {
    "backend": "Backend-разработчик (Python)",
    "frontend": "Frontend-разработчик (JavaScript/React)",
    "data": "Data Scientist / ML-инженер",
    "pm": "Менеджер продукта",
    "behavioral": "Поведенческое интервью (soft skills)",
}

LEVEL_LABELS = {
    "junior": "Junior",
    "middle": "Middle",
    "senior": "Senior",
}

INTERVIEWER_SYSTEM = (
    "Ты — опытный технический интервьюер. Ведёшь собеседование строго, "
    "но доброжелательно. Задаёшь по одному вопросу за раз, без вводных "
    "фраз вроде «отличный вопрос». Вопросы конкретные, проверяющие глубину "
    "понимания, а не зазубренные определения."
)


def question_messages(role: str, level: str, asked: list[str]) -> list[dict]:
    role_label = ROLE_LABELS.get(role, role)
    level_label = LEVEL_LABELS.get(level, level)
    asked_block = ""
    if asked:
        asked_block = (
            "\nУже заданные вопросы (не повторяй их и не дублируй темы):\n- "
            + "\n- ".join(asked)
        )
    user = (
        f"Роль кандидата: {role_label}. Уровень: {level_label}.\n"
        f"Сформулируй ОДИН новый вопрос для собеседования, подходящий этому "
        f"уровню.{asked_block}\n\n"
        "Ответь строго в формате JSON без markdown:\n"
        '{"question": "текст вопроса", "topic": "короткая тема", '
        '"hint": "одна подсказка, на что обратить внимание в ответе"}'
    )
    return [
        {"role": "system", "content": INTERVIEWER_SYSTEM},
        {"role": "user", "content": user},
    ]


def evaluation_messages(role: str, level: str, question: str,
                        answer: str) -> list[dict]:
    role_label = ROLE_LABELS.get(role, role)
    level_label = LEVEL_LABELS.get(level, level)
    user = (
        f"Роль: {role_label}. Уровень: {level_label}.\n"
        f"Вопрос: {question}\n"
        f"Ответ кандидата: {answer}\n\n"
        "Оцени ответ как интервьюер. Будь конкретным и честным. "
        "Ответь строго в формате JSON без markdown:\n"
        '{"score": число от 0 до 10, '
        '"verdict": "одно предложение — общий вердикт", '
        '"strengths": ["сильная сторона", "..."], '
        '"gaps": ["что упущено или неверно", "..."], '
        '"model_answer": "краткий образцовый ответ в 3-5 предложениях", '
        '"followup": "уточняющий вопрос, который задал бы интервьюер"}'
    )
    return [
        {"role": "system", "content": INTERVIEWER_SYSTEM},
        {"role": "user", "content": user},
    ]


def parse_json(raw: str) -> dict:
    """GigaChat иногда оборачивает JSON в ```json ... ``` — чистим."""
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("```", 2)[1]
        if text.startswith("json"):
            text = text[4:]
    text = text.strip().strip("`").strip()
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end != -1:
        text = text[start:end + 1]
    return json.loads(text)
