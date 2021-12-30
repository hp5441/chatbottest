from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from .database import Base


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    question = Column(String, unique=True, index=True)
    popularity = Column(Integer)
    is_active = Column(Boolean, default=True)

    answers = relationship("Answer", back_populates="question")


class Answer(Base):
    __tablename__ = "answers"

    id = Column(Integer, primary_key=True, index=True)
    answer = Column(String, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"))

    question = relationship("Question", back_populates="answers")