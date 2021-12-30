from typing import List, Optional

from pydantic import BaseModel


class AnswerBase(BaseModel):
    answer: str


class AnswerCreate(AnswerBase):
    pass


class Answer(AnswerBase):
    id: int
    question_id: int

    class Config:
        orm_mode = True


class QuestionBase(BaseModel):
    question: str
    popularity: int


class QuestionId(BaseModel):
    id: int


class QuestionCreate(QuestionBase):
    pass


class Question(QuestionBase):
    id: int
    is_active: bool
    answers: List[Answer] = []

    class Config:
        orm_mode = True


class QuestionMatch(Question):
    similarity: float
