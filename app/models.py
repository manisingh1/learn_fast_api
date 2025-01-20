from sqlalchemy import Boolean, Column, Integer, String, Date, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase, relationship
from app.database import Base
from typing import List


class Artist(Base):
    __tablename__ = "artist_table"
    name = Column(String(50), unique=True)

    # id = Column(Integer, primary_key=True, index=True)
    id: Mapped[int] = mapped_column(primary_key=True)
    albums: Mapped[List["Album"]] = relationship(back_populates="artist")


class Album(Base):
    __tablename__ = "album_table"
    name = Column(String(50))
    release_date = Column(Date)
    price = Column(Float)
    artist_name = Column(String(50))
    id: Mapped[int] = mapped_column(primary_key=True)
    artist_id: Mapped[int] = mapped_column(ForeignKey("artist_table.id"))
    artist: Mapped["Artist"] = relationship(back_populates="albums")
