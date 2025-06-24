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
from sqlalchemy.ext.asyncio import AsyncSession
from app.DB import get_db
import re

def quick_fix_phone_number(phone_number: str):
    print(f'Полученный номер телефона {phone_number}')
    # Удаляем все символы, кроме цифр
    digits = re.sub(r'[^0-9+]', '', phone_number)
    
    # Проверяем наличие кода страны +1
    if not digits.startswith('1'):
        digits = '1' + digits
    
    # Добавляем +
    formatted_number = f'+{digits}'
    
    # Проверка длины
    if len(formatted_number) < 12:
        print(f"❗ Недостаточно цифр в номере {formatted_number}, возможно, номер некорректный")
    
    return formatted_number

def get_region(phone_number: str):
    try:
        number_obj = phonenumbers.parse(phone_number)
        return phone_number, geocoder.description_for_number(number_obj, "en")  # вернёт, например, 'California'
    except phonenumbers.NumberParseException as e:
        print(f"Ошибка парсинга номера: {e}")
        phone_number = quick_fix_phone_number(phone_number)
        return phone_number, "Florida"

def find_closest_number(lead_number: str, telnyx_numbers: list):
    lead_number, lead_region = get_region(lead_number)
    
    for number in telnyx_numbers:
        number_region = get_region(number.phone_number)
        if number_region == lead_region:
            return number.phone_number  # Возвращаем ближайший по региону
    # fallback: если не нашли совпадений
    return lead_number, telnyx_numbers[0].phone_number

# Отправка SMS
async def send_sms(employee_username: str, lead_phone: str, message: str, db: AsyncSession = Depends(get_db)):
    # Поиск пользователя-сотрудника по логину
    user_stmt = select(User).where(User.username == employee_username)
    user_result = await db.execute(user_stmt)
    user = user_result.scalar_one_or_none()

    if not user:
        raise ValueError("Сотрудник с таким логином не найден.")
    
    # Поиск лида по номеру телефона
    lead_stmt = select(Lead).where(Lead.phone_number == lead_phone)
    lead_result = await db.execute(lead_stmt)
    lead = lead_result.scalars().first()#исправить

    if not lead:
        #result = await db.execute(select(func.count(Lead.id)))
        #count = result.scalar() + 1
        lead = Lead(
        #id = count,
        first_name="Unknown",
        phone_number=lead_phone)
        db.add(lead)
        await db.commit()
        await db.refresh(lead)


    # Получение подходящего номера Telnyx
    numbers = telnyx.PhoneNumber.list().data
    if not numbers:
        raise ValueError("Нет доступных номеров Telnyx.")
    
    lead.phone_number, number = find_closest_number(lead_number=lead.phone_number, telnyx_numbers=numbers)

    # Отправка SMS
    response = telnyx.Message.create(
        from_=number,
        to=lead.phone_number,
        text=message
    )

    # Поиск или создание коммуникации
    stmt = select(Communication).where(
        Communication.employee == user.id,
        Communication.lead == lead.id
    )
    result = await db.execute(stmt)
    communication = result.scalars().first()

    if not communication:
        communication = Communication(employee=user.id, lead=lead.id)
        db.add(communication)
        await db.flush()

    # Сохраняем сообщение
    msg = Message(
        text=message,
        time=datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None),#ЭТО ВРЕМЕННОЕ РЕШЕНИЕ
        communication_id=communication.id
    )
    db.add(msg)
    await db.commit()

    return response.to_dict()