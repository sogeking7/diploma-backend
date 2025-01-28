from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone

# Generate the current date in the required format
current_date = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

class AttendanceBase(BaseModel):
    user_id: int = Field(..., example=1)
    time_in: datetime = Field(..., example=f"{current_date}")
    time_out: Optional[datetime] = Field(None, example=f"{current_date}")

class AttendanceCreate(AttendanceBase):
    pass

class AttendanceUpdate(BaseModel):
    time_in: Optional[datetime] = Field(None, example=f"{current_date}")
    time_out: Optional[datetime] = Field(None, example=f"{current_date}")

class AttendanceOut(BaseModel):
    id: Optional[int]  # Make `id` nullable
    user_id: int
    time_in: Optional[datetime] = None  # Make `time_in` nullable
    time_out: Optional[datetime] = None  # Make `time_out` nullable
    created_at: Optional[datetime] = None  # Make `created_at` nullable

    class Config:
        from_attributes = True  # For Pydantic v2 compatibility
