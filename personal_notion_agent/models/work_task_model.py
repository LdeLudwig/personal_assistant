from pydantic import BaseModel, Field, model_validator
from typing import Optional, Literal
from datetime import datetime, date

from skills.utils.datetime_utils import ensure_sp_aware, isoformat_sp


class WorkTask(BaseModel):
    name: str
    project: str = Field(default_factory=str)
    priority: Optional[Literal["High", "Medium", "Low"]] = None
    status: Optional[
        Literal[
            "To do",
            "Refining",
            "Paused",
            "Postponed",
            "In progress",
            "Pull Request",
            "Acceptance",
            "Done",
        ]
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
        props["Project"] = {"relation": [{"id": self.project}]}
        if self.priority:
            props["Priority"] = {"select": {"name": self.priority}}
        if self.status:
            props["Status"] = {"status": {"name": self.status}}
        if self.start or self.end:
            props["deadline"] = {
                "date": {
                    "start": isoformat_sp(self.start),
                    "end": isoformat_sp(self.end),
                }
            }
        return {"parent": {"database_id": database_id}, "properties": props}
