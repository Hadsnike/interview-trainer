"""Тренажёр собеседований — backend на FastAPI поверх GigaChat.

Запуск:  uvicorn app:app --reload
Без ключа GIGACHAT_AUTH_KEY работает demo-режим с заготовленными ответами,
чтобы проект можно было запустить и посмотреть сразу.
"""

import random
from pathlib import Path

from dotenv import load_dotenv

# Грузим .env из корня проекта ДО импорта клиента: gigachat_client читает
# переменные окружения в момент импорта, поэтому порядок важен.
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from gigachat_client import client, GigaChatError
import prompts

app = FastAPI(title="Interview Trainer")

FRONTEND = Path(__file__).resolve().parent.parent / "frontend"


class QuestionReq(BaseModel):
    role: str = "backend"
    level: str = "middle"
    asked: list[str] = []


class EvalReq(BaseModel):
    role: str = "backend"
    level: str = "middle"
    question: str
    answer: str


# --- demo-режим -----------------------------------------------------------

DEMO_QUESTIONS = [
    {"question": "Чем процесс отличается от потока, и когда выбрать один, а не другой?",
     "topic": "Конкурентность", "hint": "Память, изоляция, накладные расходы на переключение."},
    {"question": "Что произойдёт при добавлении индекса на часто обновляемый столбец?",
     "topic": "Базы данных", "hint": "Баланс между скоростью чтения и стоимостью записи."},
    {"question": "Как бы вы диагностировали утечку памяти в продакшене?",
     "topic": "Эксплуатация", "hint": "Инструменты, гипотезы, метрики во времени."},
]


def demo_eval(answer: str) -> dict:
    score = min(10, max(2, len(answer.split()) // 8 + random.randint(1, 3)))
    return {
        "score": score,
        "verdict": "Demo-режим: ответ принят, ключ GigaChat не подключён.",
        "strengths": ["Ответ по существу вопроса"],
        "gaps": ["Подключите GIGACHAT_AUTH_KEY для настоящей оценки"],
        "model_answer": "Это заглушка. С реальным ключом здесь будет образцовый ответ от GigaChat.",
        "followup": "Можете привести конкретный пример из практики?",
    }


# --- API ------------------------------------------------------------------

@app.get("/api/health")
def health():
    return {"configured": client.configured}


@app.post("/api/question")
def get_question(req: QuestionReq):
    if not client.configured:
        pool = [q for q in DEMO_QUESTIONS if q["question"] not in req.asked]
        return random.choice(pool or DEMO_QUESTIONS)
    try:
        raw = client.chat(prompts.question_messages(req.role, req.level, req.asked),
                          temperature=0.9)
        return prompts.parse_json(raw)
    except (GigaChatError, ValueError) as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.post("/api/evaluate")
def evaluate(req: EvalReq):
    if not req.answer.strip():
        raise HTTPException(status_code=400, detail="Пустой ответ")
    if not client.configured:
        return demo_eval(req.answer)
    try:
        raw = client.chat(
            prompts.evaluation_messages(req.role, req.level, req.question, req.answer),
            temperature=0.3)
        return prompts.parse_json(raw)
    except (GigaChatError, ValueError) as e:
        raise HTTPException(status_code=502, detail=str(e))


# --- статика ---------------------------------------------------------------

@app.get("/")
def index():
    return FileResponse(FRONTEND / "index.html")


app.mount("/", StaticFiles(directory=FRONTEND), name="static")
