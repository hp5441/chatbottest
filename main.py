from typing import List, Optional
import spacy

from fastapi import Depends, FastAPI, HTTPException, Header

from sqlalchemy.orm import Session
from sql_controller import crud, models, schemas
from sql_controller.database import SessionLocal, engine
from config import Settings


models.Base.metadata.create_all(bind=engine)

app = FastAPI()
nlp = spacy.load("en_core_web_md")
print("new")

settings = Settings()
token = settings.token


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def process_text(text):
    doc = nlp(text.lower())
    result = []
    for token in doc:
        if token.text in nlp.Defaults.stop_words:
            continue
        if token.is_punct:
            continue
        if token.lemma_ == '-PRON-':
            continue
        result.append(token.lemma_)
    return " ".join(result)


def load_nlp_memory():
    try:
        db = SessionLocal()
        questions_list = crud.get_questions(db)
        nlp_dict = dict(
            map(lambda q: (q.id, nlp(process_text(q.question))), questions_list))
        return questions_list, nlp_dict
    finally:
        db.close()


questions_list, nlp_dict = load_nlp_memory()
for question in questions_list:
    print(question.question)


@app.post("/startSession", response_model=List[schemas.Question])
async def get_top(db: Session = Depends(get_db)):
    return crud.get_top_questions(db)


@app.post("/allQuestions", response_model=List[schemas.Question])
async def get_all_questions(db: Session = Depends(get_db), x_token: Optional[str] = Header(None)):
    if x_token==token:
        return crud.get_questions(db, 0)
    else:
        raise HTTPException(status_code=403, detail="Access denied")


@app.post("/getSuggestedQuestions", response_model=List[schemas.Question])
async def get_suggestions(q: schemas.QuestionBase, db: Session = Depends(get_db)):
    suggested_list = []
    q_ind = 0

    while q_ind < len(questions_list) and len(suggested_list) < 5:
        if q.question in questions_list[q_ind].question:
            suggested_list.append(crud.get_question(
                db, questions_list[q_ind].id))
        q_ind += 1

    return suggested_list


@app.post("/getMatch", response_model=List[schemas.QuestionMatch])
async def get_match(q: schemas.QuestionId, db: Session = Depends(get_db)):
    from heapq import heappush, heappop
    q_nlp = nlp(q.question)
    max_similar_qs = []

    for key, value in nlp_dict.items():
        heappush(max_similar_qs, (-1*q_nlp.similarity(value), key))

    top_five = []
    while len(max_similar_qs) > 0 and len(top_five) < 5:
        score, question_id = heappop(max_similar_qs)
        db_question = crud.get_question(db, question_id)
        if db_question:
            top_five.append({"similarity": -1*score, **
                            schemas.Question.from_orm(db_question).dict()})
    return top_five


@app.post("/getQuestionAns", response_model=schemas.Question)
async def get_ans(question_id: schemas.QuestionId, db: Session = Depends(get_db)):
    db_question = crud.get_question(db, question_id.id)
    if not db_question:
        raise HTTPException(status_code=404, detail="Question not found")
    return db_question


@app.post("/endSession")
async def read_root():
    return {"end": "Session"}


@app.post("/createQuestion", response_model=schemas.Question)
async def create_question(question: schemas.QuestionCreate, db: Session = Depends(get_db), x_token: Optional[str] = Header(None)):
    if x_token == token:
        return crud.create_question(db, question)
    else:
        raise HTTPException(status_code=403, detail="Access denied")


@app.post("/createAnswer/{question_id}/", response_model=schemas.Answer)
async def create_answer(answer: schemas.AnswerCreate, question_id: int, db: Session = Depends(get_db), x_token: Optional[str] = Header(None)):
    db_question = crud.get_question(db, question_id)
    if not db_question:
        return HTTPException(status_code=404, detail="Question not found")
    else:
        if x_token == token:
            return crud.create_answer(db, answer, question_id)
        else:
            raise HTTPException(status_code=403, detail="Access denied")
