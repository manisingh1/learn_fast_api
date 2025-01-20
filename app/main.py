from fastapi import FastAPI, HTTPException, Depends, status
from pydantic import BaseModel
from typing import Annotated
from app import models
from app.database import engine, SessionLocal
from sqlalchemy.orm import Session
from datetime import date
from typing import List

app = FastAPI()
models.Base.metadata.create_all(bind=engine)


class AlbumBase(BaseModel):
    name: str
    release_date: date
    price: float
    artist_name: str


class ArtistBase(BaseModel):
    name: str


class ArtistWithAlbums(BaseModel):
    albums: List[AlbumBase] = []


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]


# get all artists
@app.get("/artists/", status_code=status.HTTP_200_OK)
async def get_artists(db: db_dependency):
    artists = db.query(models.Artist).all()
    return artists


# create an artist
@app.post("/artists/", status_code=status.HTTP_201_CREATED)
async def create_artist(artist: ArtistBase, db: db_dependency):
    db_artist = models.Artist(**artist.model_dump())
    db.add(db_artist)
    db.commit()
    db.refresh(db_artist)
    return db_artist


# delete an artist
@app.delete("/artists/{artist_id}", status_code=status.HTTP_200_OK)
async def delete_artist(artist_id: int, db: db_dependency):
    db_artist = db.query(models.Artist).filter(models.Artist.id == artist_id).first()
    if db_artist is None:
        raise HTTPException(status_code=404, detail="Artist was not found")
    db.delete(db_artist)
    db.commit()


# refactored to fix tests
# # create an album
# @app.post("/albums", status_code=status.HTTP_201_CREATED)
# async def create_album(album: AlbumBase, db: db_dependency):
#     db_album = models.Album(**album.model_dump())
#     db.add(db_album)
#     db.commit()
#     db.refresh(db_album)
#     return db_album


# updated request url
@app.post("/albums/", status_code=status.HTTP_201_CREATED)
async def create_album(album: AlbumBase, db: db_dependency):
    artist = (
        db.query(models.Artist).filter(models.Artist.name == album.artist_name).first()
    )
    if not artist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Artist with name ({album.artist_name}) not found",
        )
    else:
        try:
            db_album = models.Album(
                name=album.name,
                release_date=album.release_date,
                price=album.price,
                artist_id=artist.id,
                artist_name=album.artist_name,
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{e}",
            )
        db.add(db_album)
        db.commit()
        db.refresh(db_album)

        return db_album


# get albums for an artist
@app.get("/albums/{artist_name}", status_code=status.HTTP_200_OK)
async def read_artist_with_albums(
    artist_name: str,
    db: db_dependency,
    min_price: float = None,
    max_price: float = None,
    min_date: date = None,
    max_date: date = None,
):
    artist = db.query(models.Artist).filter(models.Artist.name == artist_name).first()
    if not artist:
        raise HTTPException(status_code=404, detail="Artist was not found")
    albums = retrieve_albums(db, artist, min_price, max_price, min_date, max_date)
    return albums


def retrieve_albums(db, artist, min_price, max_price, min_date, max_date):
    query = db.query(models.Album).filter(models.Album.artist_id == artist.id)

    if min_date:
        query = query.filter(models.Album.release_date >= min_date)
    if max_date:
        query = query.filter(models.Album.release_date <= max_date)
    if min_price:
        query = query.filter(models.Album.price >= min_price)
    if max_price:
        query = query.filter(models.Album.price <= max_price)

    albums = query.all()
    return albums


@app.get("/")
async def root():
    return {"message": "Hello World"}
