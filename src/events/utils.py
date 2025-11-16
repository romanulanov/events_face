import os

import requests

NOTIFICATIONS_URL = "https://notifications.k3scluster.tech/api/notifications/"
NOTIFICATIONS_TOKEN = os.environ['NOTIFICATIONS_TOKEN']
OWNER_ID = os.environ['OWNER_ID']


def send_confirmation_email(
        email: str,
        full_name: str,
        confirmation_code: str,
        event_name: str
     ) -> bool:
    payload = {
        "owner_id": OWNER_ID,
        "email": email,
        "subject": f"Регистрация на мероприятие: {event_name}",
        "message": f"Здравствуйте, {full_name}!\n\n"
        f"Ваш код подтверждения: {confirmation_code}\n\n"
        "Спасибо за регистрацию!"
    }

    headers = {
        "Authorization": f"Bearer {NOTIFICATIONS_TOKEN}",
        "Content-Type": "application/json",
    }

    response = requests.post(NOTIFICATIONS_URL, json=payload, headers=headers)

    return response.status_code == 200
