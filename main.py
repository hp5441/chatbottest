import html
import json
from typing import List, Optional
import spacy
from bleach import linkify
from textile import textile

from fastapi import Depends, FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy.orm import Session
from sql_controller import crud, models, schemas
from sql_controller.database import SessionLocal, engine
from config import Settings

from utils import KMPSearch, computeLPSArray


models.Base.metadata.create_all(bind=engine)

app = FastAPI()

origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:8080",
    "https://hcisingapore.gov.in"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


def process_question(question: models.Question, match=""):
    processed_question = question.question
    if len(match):
        pattern_index = KMPSearch(match.lower(), processed_question.lower())
        if pattern_index is not None:
            processed_question = processed_question[:pattern_index]+"<em>"+processed_question[pattern_index:pattern_index+len(match)]+"</em>"+processed_question[pattern_index+len(match):]
            print(processed_question)
    question.question = textile(processed_question, html_type="html5")
    return question


def process_answer(answer : models.Answer):
    processed_answer = json.loads(answer.answer).strip()
    if processed_answer[0]!="<" and processed_answer[-1]!=">":
        html_text = linkify("<p>"+processed_answer+"</p>")
    else:
        html_text=linkify(processed_answer)
    answer.answer = html.escape(html_text) 
    return answer
    


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
    q.question = q.question.strip()
    global questions_list, nlp_dict
    
    if len(questions_list)==0:
        questions_list, nlp_dict = load_nlp_memory()

    while len(q.question)>=3 and q_ind < len(questions_list) and len(suggested_list) < 5:
        if q.question.lower() in questions_list[q_ind].question.lower():
            fetched_question = crud.get_question(
                db, questions_list[q_ind].id)
            fetched_question = process_question(fetched_question, q.question)
            fetched_question.answers = [process_answer(answer) for answer in fetched_question.answers] 
            suggested_list.append(fetched_question)
        q_ind += 1

    return suggested_list


@app.post("/getMatch", response_model=schemas.QuestionsMatch)
async def get_match(q: schemas.QuestionBase, db: Session = Depends(get_db)):
    from heapq import heappush, heappop
    q_nlp = nlp(process_text(q.question))
    max_similar_qs = []

    for key, value in nlp_dict.items():
        heappush(max_similar_qs, (-1*q_nlp.similarity(value), key))

    relevant=[]
    others=[]
    
    while len(max_similar_qs) > 0 and (len(relevant)+len(others))< 5:
        score, question_id = heappop(max_similar_qs)
        db_question = crud.get_question(db, question_id)
        if db_question:
            db_question = process_question(db_question)
            db_question.answers = [process_answer(answer) for answer in db_question.answers]
            if (-1*score)>=0.75:
                relevant.append({"similarity": -1*score, **
                                schemas.Question.from_orm(db_question).dict()})
            else:
                others.append({"similarity": -1*score, **
                                schemas.Question.from_orm(db_question).dict()})
    return {'relevant':relevant, 'others':others}


@app.post("/getQuestionAns", response_model=schemas.Question)
async def get_ans(question_id: schemas.QuestionId, db: Session = Depends(get_db)):
    db_question = crud.get_question(db, question_id.id)
    if not db_question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    db_question = process_question(db_question)
    db_question.answers = [process_answer(answer) for answer in db_question.answers]
    return db_question


@app.post("/endSession")
async def read_root():
    return {"end": "Session"}


@app.post("/createQuestion", response_model=schemas.Question)
async def create_question(question: schemas.QuestionCreate, db: Session = Depends(get_db), x_token: Optional[str] = Header(None)):
    try:
        if x_token == token:
            return crud.create_question(db, question)
        else:
            raise HTTPException(status_code=403, detail="Access denied")
    except Exception as e:
        raise HTTPException(status_code=422, detail="Error while creating entry")
    finally:
        global questions_list, nlp_dict
        questions_list, nlp_dict = load_nlp_memory()


@app.post("/createAnswer/{question_id}/", response_model=schemas.Answer)
async def create_answer(answer: schemas.AnswerCreate, question_id: int, db: Session = Depends(get_db), x_token: Optional[str] = Header(None)):
    db_question = crud.get_question(db, question_id)
    if not db_question:
        return HTTPException(status_code=404, detail="Question not found")
    else:
        try:
            if x_token == token:
                return crud.create_answer(db, answer, question_id)
            else:
                raise HTTPException(status_code=403, detail="Access denied")
        except Exception as e:
            raise HTTPException(status_code=422, detail="Error while creating entry")
        finally:
            global questions_list, nlp_dict
            questions_list, nlp_dict = load_nlp_memory()
            
            
@app.post("/deleteAnswer/{answer_id}/")
async def delete_answer(answer_id: int, db: Session = Depends(get_db), x_token: Optional[str] = Header(None)):
    db_answer = crud.get_answer(db, answer_id)
    if not db_answer:
        return HTTPException(status_code=404, detail="Question not found")
    else:
        try:
            if x_token == token:
                return crud.delete_answer(db, answer_id)
            else:
                raise HTTPException(status_code=403, detail="Access denied")
        except Exception as e:
            raise HTTPException(status_code=422, detail="Error while creating entry")
        finally:
            global questions_list, nlp_dict
            questions_list, nlp_dict = load_nlp_memory()
