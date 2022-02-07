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


class QuestionId(BaseModel):
    id: int


class QuestionCreate(QuestionBase):
    popularity: int
    is_keyword: bool = False


class Question(QuestionCreate):
    id: int
    is_active: bool
    answers: List[Answer] = []

    class Config:
        orm_mode = True


class QuestionMatch(Question):
    similarity: float
    
class QuestionsMatch(BaseModel):
    relevant: List[QuestionMatch] = []
    others: List[QuestionMatch] = []
