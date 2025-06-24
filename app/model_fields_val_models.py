from pydantic import BaseModel

class SendSMSInput(BaseModel):
    employee_username: str
    lead_phone: str
    message: str