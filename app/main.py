import email
from typing import Optional, List
from fastapi import FastAPI, Body, Response, status, HTTPException, Depends
from pydantic import BaseModel
from random import randrange
import psycopg2
from psycopg2.extras import RealDictCursor
import time
from . import models, schemas, utils
from .database import engine, get_db, try_connection
from sqlalchemy.orm import Session
from sqlalchemy import insert, update, delete
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

try_connection()

my_posts = [{"title": "title of post 1", "content": "content of post 1", "id": 1},
            {"title": "title of post 2", "content": "content of post 2", "id": 2}]


def find_post(id):
    for p in my_posts:
        if p["id"] == id:
            return p


def find_index_post(id: int):
    for i, p in enumerate(my_posts):
        if p['id'] == id:
            return int(i)
        else:
            return 'id not found'


@app.get("/")  # path operation
def root():
    return {"message": "Hello World"}


"""
@app.get("/sqlalchemy")
def test_posts(db: Session = Depends(get_db)):
    posts=db.query(models.Post).all()
    return {"data": posts}
"""


@app.get("/posts", response_model=List[schemas.Post])
def get_posts(db: Session = Depends(get_db)):
    posts = db.query(models.Post).all()
    """
    cursor.execute("SELECT * FROM posts")
    posts = cursor.fetchall()
    """
    return posts


@app.post("/posts", status_code=status.HTTP_201_CREATED, response_model=schemas.Post)
def create_posts(post: schemas.PostCreate, db: Session = Depends(get_db)):
    """
    post_dict = post.dict()
    post_dict['id'] = randrange(0, 100000)
    my_posts.append(post_dict)
    """
    # cursor.execute(""" INSERT INTO posts (title, content, published) VALUES (%s, %s, %s) RETURNING *""", (post.title, post.content, post.published))
    # new_post = cursor.fetchone()
    # conn.commit()
    new_post = models.Post(**post.dict())
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return new_post


@app.get("/posts/{id}", response_model=schemas.Post)
def get_post(id: int, db: Session = Depends(get_db)):
    """
    post = find_post(id)
    """
    # cursor.execute(""" SELECT * FROM posts WHERE id=%s """, [id])
    # post = cursor.fetchone()
    # conn.commit()
    post = db.query(models.Post).filter(models.Post.id == id).first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"post with id {id} not found")
    return post


@app.delete("/posts/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(id: int, db: Session = Depends(get_db)):
    # cursor.execute(""" DELETE FROM posts WHERE id =%s RETURNING *""", [id])
    # deleted_post = cursor.fetchone()
    # conn.commit()
    """
    index = find_index_post(id)
    my_posts.pop(index)
    """
    post = db.query(models.Post).filter(models.Post.id == id)
    if post.first() == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"post with id {id} does not exist")
    post.delete(synchronize_session=False)
    db.commit()
    return post, Response(status_code=status.HTTP_204_NO_CONTENT)


@app.put("/posts/{id}", response_model=schemas.Post)
def update_post(id: int, updated_post: schemas.PostCreate, db: Session = Depends(get_db)):
    """
    index = find_index_post(id)
    post_dict = post.dict()
    post_dict['id'] = id
    my_posts[index] = post_dict
    """
    # cursor.execute(""" UPDATE posts SET title =%s, content=%s WHERE id=%s RETURNING * """, (post.title, post.content, (id)))
    # updated_post = cursor.fetchone()
    # conn.commit()
    post_query = db.query(models.Post).filter(models.Post.id == id)
    post = post_query.first()

    if post == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"post with id {id} does not exist")
    else:
        post_query.update(updated_post.dict(), synchronize_session=False)
        db.commit()
    return post_query.first(), Response(status_code=status.HTTP_201_CREATED)


@app.post("/users", status_code=status.HTTP_201_CREATED, response_model=schemas.UserOut)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    hashed_password = utils.hash(user.password)
    user.password = hashed_password
    new_user = models.User(**user.dict())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user
