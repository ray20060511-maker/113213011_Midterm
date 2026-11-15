from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
import models
import database

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="投稿與審查系統")

class ArticleCreate(BaseModel):
    title: str
    category: str
    content: str

class ArticleUpdate(BaseModel):
    title: str
    category: str
    content: str

@app.get("/", summary="前端首頁")
def read_index():
    return FileResponse("index.html")

@app.post("/authors/{author_id}/articles", summary="新增投稿")
def create_article(author_id: int, article: ArticleCreate, db: Session = Depends(database.get_db)):
    new_article = models.Article(
        title=article.title,
        category=article.category,
        content=article.content,
        status="編輯中",
        author_id=author_id
    )
    db.add(new_article)
    db.commit()
    db.refresh(new_article)
    return {"message": "稿件建立成功 (編輯中)", "article": new_article}

@app.get("/authors/{author_id}/articles", summary="查看投稿稿件清單")
def get_author_articles(author_id: int, db: Session = Depends(database.get_db)):
    articles = db.query(models.Article).filter(models.Article.author_id == author_id).all()
    return articles

@app.put("/articles/{article_id}", summary="編輯投稿 (僅限編輯中)")
def update_article(article_id: int, article_update: ArticleUpdate, db: Session = Depends(database.get_db)):
    article = db.query(models.Article).filter(models.Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="找不到該稿件")
    if article.status != "編輯中":
        raise HTTPException(status_code=400, detail="只能編輯『編輯中』狀態的稿件")
    
    article.title = article_update.title
    article.category = article_update.category
    article.content = article_update.content
    db.commit()
    return {"message": "稿件更新成功"}

@app.delete("/articles/{article_id}", summary="刪除編輯中稿件")
def delete_article(article_id: int, db: Session = Depends(database.get_db)):
    article = db.query(models.Article).filter(models.Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="找不到該稿件")
    if article.status != "編輯中":
        raise HTTPException(status_code=400, detail="只能刪除『編輯中』狀態的稿件")
    
    db.delete(article)
    db.commit()
    return {"message": "稿件已刪除"}

@app.post("/articles/{article_id}/submit", summary="送出投稿 (編輯中 => 審查中)")
def submit_article(article_id: int, db: Session = Depends(database.get_db)):
    article = db.query(models.Article).filter(models.Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="找不到該稿件")
    if article.status != "編輯中":
        raise HTTPException(status_code=400, detail="只有『編輯中』的稿件可以送出審查")
    
    article.status = "審查中"
    db.commit()
    return {"message": "已成功送出投稿，目前狀態為：審查中"}




@app.get("/editor/pending-articles", summary="查看待審查清單")
def get_pending_articles(db: Session = Depends(database.get_db)):
    articles = db.query(models.Article).filter(models.Article.status == "審查中").all()
    return articles

@app.post("/editor/articles/{article_id}/approve", summary="審核通過 (審查中 => 已通過)")
def approve_article(article_id: int, db: Session = Depends(database.get_db)):
    article = db.query(models.Article).filter(models.Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="找不到該稿件")
    if article.status != "審查中":
        raise HTTPException(status_code=400, detail="該稿件不在審查中")
    
    article.status = "已通過"
    db.commit()
    return {"message": "稿件已審核通過"}

@app.post("/editor/articles/{article_id}/reject", summary="退回稿件 (審查中 => 編輯中)")
def reject_article(article_id: int, db: Session = Depends(database.get_db)):
    article = db.query(models.Article).filter(models.Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="找不到該稿件")
    if article.status != "審查中":
        raise HTTPException(status_code=400, detail="該稿件不在審查中")
    
    article.status = "編輯中"
    db.commit()
    return {"message": "稿件已被退回至編輯中"}