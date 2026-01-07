from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class User:
    user_id: int
    first_name: str
    last_name: str
    username: str
    last_active: datetime
    created_at: datetime 
    vip_created: Optional[datetime] = None 
    is_vip: bool = False
    is_active: bool = True
