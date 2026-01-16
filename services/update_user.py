import datetime
import pytz
from services.logic import User
from services.database import DB_Save_User, DB_Get_User
from config import (
    # DEBUG, 
    TIMEZONE)


def update_User_Activity_Logic(tg_user):
    user_id = tg_user.id
    first_name = tg_user.first_name
    last_name = tg_user.last_name or ""
    username = tg_user.username or "Anonym"

    tz = pytz.timezone(TIMEZONE)
    now = datetime.datetime.now(tz)

    user_db = DB_Get_User(user_id)

    if user_db:
        # user lama
        user_model = User(
            user_id=user_id,
            first_name=first_name,
            last_name=last_name,
            username=username,
            is_vip=user_db.is_vip,
            is_active=user_db.is_active,
            last_active=now,
            created_at=user_db.created_at
        )
    else:
        # user baru
        user_model = User(
            user_id=user_id,
            first_name=first_name,
            last_name=last_name,
            username=username,
            is_vip=False,
            is_active=True,
            last_active=now,
            created_at=now
        )

    DB_Save_User(user_model)

    # if DEBUG:
    #     print(f"[LOGIC] User activity updated: {user_id}")

    return user_model
