from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String, unique=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    api_key: Mapped[str] = mapped_column(String, unique=True, index=True)

class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str | None] = mapped_column(String(100))
    phone_number: Mapped[str] = mapped_column(String(20))
    landline_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    email: Mapped[str | None] = mapped_column(String(100))
    address: Mapped[str | None] = mapped_column(String(255))
    city: Mapped[str | None] = mapped_column(String(100))
    state: Mapped[str | None] = mapped_column(String(100))
    occupation: Mapped[str | None] = mapped_column(String(100))
    business_name: Mapped[str | None] = mapped_column(String(150))

class Communication(Base):
    __tablename__ = "communications"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    lead: Mapped[int] = mapped_column(Integer, ForeignKey("leads.id"))

    employee_user = relationship("User", foreign_keys=[employee])
    lead_obj = relationship("Lead", foreign_keys=[lead])

    messages = relationship("Message", back_populates="communication")

class Message(Base):
    __tablename__ = "messages"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    time: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    text: Mapped[str] = mapped_column(Text)

    communication_id: Mapped[int] = mapped_column(Integer, ForeignKey("communications.id"))
    communication = relationship("Communication", back_populates="messages")

    metadata_ = relationship("MessageMetadata", back_populates="message", uselist=False)

class MessageMetadata(Base):
    __tablename__ = "message_metadata"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sender: Mapped[str | None] = mapped_column(String(50), nullable=True)
    received_via: Mapped[str | None] = mapped_column(String(20), nullable=True)
    
    message_id: Mapped[int] = mapped_column(Integer, ForeignKey("messages.id"))
    message = relationship("Message", back_populates="metadata_")