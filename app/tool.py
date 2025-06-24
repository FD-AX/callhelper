from langchain.agents import Tool
from app.db_models import User, Lead, Communication
import telnyx
import phonenumbers
from phonenumbers import geocoder
import os, datetime
from fastapi import Request, APIRouter, WebSocket, Depends
from dotenv import load_dotenv
from app.db_models import Communication, Message, Lead, User
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.DB import get_db
from app.qdrant_conn import save_message_to_qdrant
import re

load_dotenv()
telnyx.api_key = os.getenv("TELNYX_API")

def quick_fix_phone_number(phone_number: str):
    digits = re.sub(r'[^0-9+]', '', phone_number)
    if not digits.startswith('1'):
        digits = '1' + digits
    return f'+{digits}'


def get_region(phone_number: str):
    try:
        number_obj = phonenumbers.parse(phone_number)
        return phone_number, geocoder.description_for_number(number_obj, "en")
    except phonenumbers.NumberParseException:
        return quick_fix_phone_number(phone_number), "Florida"


def find_closest_number(lead_number: str, telnyx_numbers: list):
    lead_number, lead_region = get_region(lead_number)
    for number in telnyx_numbers:
        number_region = get_region(number.phone_number)
        if number_region == lead_region:
            return lead_number, number.phone_number
    return lead_number, telnyx_numbers[0].phone_number


def send_sms(employee_username: str, lead_phone: str, message: str, db: Session = next(get_db())):
    # Получаем пользователя
    user = db.execute(
        select(User).where(User.username == employee_username)
    ).scalar_one_or_none()

    if not user:
        raise ValueError("Сотрудник не найден")

    # Получаем или создаём лида
    lead = db.execute(
        select(Lead).where(Lead.phone_number == lead_phone)
    ).scalar_one_or_none()

    if not lead:
        lead = Lead(first_name="Unknown", phone_number=lead_phone)
        db.add(lead)
        db.commit()
        db.refresh(lead)

    # Получаем подходящий номер
    numbers = telnyx.PhoneNumber.list().data
    if not numbers:
        raise ValueError("Нет доступных номеров Telnyx.")

    lead.phone_number, from_number = find_closest_number(lead.phone_number, numbers)

    # Отправляем сообщение
    response = telnyx.Message.create(
        from_=from_number,
        to=lead.phone_number,
        text=message
    )

    # Находим или создаём Communication
    communication = db.execute(
        select(Communication).where(
            Communication.employee == user.id,
            Communication.lead == lead.id
        )
    ).scalar_one_or_none()

    if not communication:
        communication = Communication(employee=user.id, lead=lead.id)
        db.add(communication)
        db.flush()

    # Сохраняем сообщение
    msg = Message(
        text=message,
        time=datetime.datetime.utcnow(),
        communication_id=communication.id
    )
    db.add(msg)
    db.commit()

    try:
        save_message_to_qdrant(message, communication.id)
    except:
        pass

    return response.to_dict()