import uuid
import random
from faker import Faker
from datetime import datetime, timedelta

def get_random_datetime(within_days=300):
    now = datetime.now()
    random_days = random.randint(0, within_days)
    random_seconds = random.randint(0, 86400)
    return now - timedelta(days=random_days, seconds=random_seconds)

fake = Faker('ko_KR')

def generate_fake_user():
    user_uuid = str(uuid.uuid4())
    email = fake.unique.email()
    password = "fake_pw"  # 필요 시 hash(password) 처리
    nickname = fake.unique.user_name()
    name = fake.name()
    birthdate = fake.date_of_birth(minimum_age=20, maximum_age=60).strftime('%Y-%m-%d')
    phone_number = fake.phone_number()
    gender = random.choice(['MALE', 'FEMALE'])
    state = "ACTIVE"
    created_at = get_random_datetime()
    updated_at = created_at

    return (
        user_uuid, email, password, nickname, name,
        birthdate, phone_number, gender, state, created_at, updated_at
    )