from pydantic.types import Json
import json
from sqlalchemy.orm import Session

from . import models, schemas


def get_questions(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Question).offset(skip).all()

def get_top_questions(db: Session, limit: int = 5):
    return db.query(models.Question).order_by(models.Question.popularity).limit(limit).all()

def get_question(db: Session, question_id: int):
    return db.query(models.Question).filter(models.Question.id==question_id).first()


def create_question(db: Session, question: schemas.QuestionCreate):
    
    db_question = models.Question(**question.dict())
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    return db_question


def get_answers(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Answer).offset(skip).all()

def get_answer(db: Session, answer_id:int):
    return db.query(models.Answer).filter(models.Answer.id==answer_id).first()


def create_answer(db: Session, answer: schemas.AnswerCreate, question_id: int):
    db_answer = models.Answer(answer=json.dumps(answer.answer, strict=False, default=str), question_id=question_id)
    db.add(db_answer)
    db.commit()
    db.refresh(db_answer)
    return db_answer


def delete_answer(db: Session, answer_id: int):
    db_answer = db.query(models.Answer).filter(models.Answer.id==answer_id).delete(synchronize_session=False)
    db.commit()
    return db_answer