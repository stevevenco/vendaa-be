from ninja import Schema


class UserInput(Schema):
    email: str
    password: str


class OTPInput(Schema):
    otp: int
