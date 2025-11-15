from datetime import datetime, date
from pydantic import BaseModel, Field, model_validator
from typing import Optional, Literal

from skills.utils.datetime_utils import ensure_sp_aware, isoformat_sp


class PersonalTask(BaseModel):
    name: str
    priority: Optional[Literal["High", "Medium", "Low"]] = None
    work_tasks: Optional[list[str]] = Field(default_factory=list)
    status: Optional[
        Literal["Paused", "Not started", "In progress", "Done", "Undone"]
    ] = None
    start: Optional[str | date | datetime] = None
    end: Optional[str | date | datetime] = None

    def __init__(self, data: dict):
        super().__init__(**data)

    @model_validator(mode="after")
    def validate_date_order(self):
        start_dt = ensure_sp_aware(self.start)
        end_dt = ensure_sp_aware(self.end)
        if start_dt is not None and end_dt is not None and end_dt < start_dt:
            raise ValueError("End date/time cannot be before start date/time.")
        return self

    def to_create_payload(self, database_id: str) -> dict:
        props: dict = {
            "Name": {"title": [{"text": {"content": self.name}}]},
        }
        if self.priority:
            props["Priority"] = {"select": {"name": self.priority}}
        if self.work_tasks:
            props["Work Tasks"] = {"relation": [{"id": pid} for pid in self.work_tasks]}
        if self.status:
            props["Status"] = {"status": {"name": self.status}}
        if self.start or self.end:
            props["Date"] = {
                "date": {
                    "start": isoformat_sp(self.start),
                    "end": isoformat_sp(self.end),
                }
            }
        return {"parent": {"database_id": database_id}, "properties": props}
