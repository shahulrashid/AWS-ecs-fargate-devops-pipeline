"""Storage layer.

Uses DynamoDB when DYNAMODB_TABLE is set, otherwise an in-memory store
(handy for local development and unit tests).
"""
import os
import uuid
from typing import Dict, List, Optional, Protocol

from .models import Task, TaskCreate, TaskUpdate


class TaskRepository(Protocol):
    def list(self) -> List[Task]: ...
    def get(self, task_id: str) -> Optional[Task]: ...
    def create(self, data: TaskCreate) -> Task: ...
    def update(self, task_id: str, data: TaskUpdate) -> Optional[Task]: ...
    def delete(self, task_id: str) -> bool: ...
    def ping(self) -> bool: ...


class InMemoryRepository:
    def __init__(self) -> None:
        self._items: Dict[str, Task] = {}

    def list(self) -> List[Task]:
        return list(self._items.values())

    def get(self, task_id: str) -> Optional[Task]:
        return self._items.get(task_id)

    def create(self, data: TaskCreate) -> Task:
        task = Task(task_id=str(uuid.uuid4()), **data.model_dump())
        self._items[task.task_id] = task
        return task

    def update(self, task_id: str, data: TaskUpdate) -> Optional[Task]:
        current = self._items.get(task_id)
        if current is None:
            return None
        updated = current.model_copy(update=data.model_dump(exclude_unset=True))
        self._items[task_id] = updated
        return updated

    def delete(self, task_id: str) -> bool:
        return self._items.pop(task_id, None) is not None

    def ping(self) -> bool:
        return True


class DynamoDBRepository:
    def __init__(self, table_name: str, region: Optional[str] = None) -> None:
        import boto3  # lazy import so local dev doesn't need AWS

        self._client = boto3.client("dynamodb", region_name=region)
        self._table_name = table_name
        self._table = boto3.resource("dynamodb", region_name=region).Table(table_name)

    @staticmethod
    def _to_task(item: dict) -> Task:
        return Task(
            task_id=item["task_id"],
            title=item["title"],
            description=item.get("description", ""),
            status=item.get("status", "pending"),
        )

    def list(self) -> List[Task]:
        items, kwargs = [], {}
        while True:
            resp = self._table.scan(**kwargs)
            items.extend(resp.get("Items", []))
            if "LastEvaluatedKey" not in resp:
                break
            kwargs["ExclusiveStartKey"] = resp["LastEvaluatedKey"]
        return [self._to_task(i) for i in items]

    def get(self, task_id: str) -> Optional[Task]:
        item = self._table.get_item(Key={"task_id": task_id}).get("Item")
        return self._to_task(item) if item else None

    def create(self, data: TaskCreate) -> Task:
        task = Task(task_id=str(uuid.uuid4()), **data.model_dump())
        self._table.put_item(Item=task.model_dump(mode="json"))
        return task

    def update(self, task_id: str, data: TaskUpdate) -> Optional[Task]:
        current = self.get(task_id)
        if current is None:
            return None
        updated = current.model_copy(update=data.model_dump(exclude_unset=True))
        self._table.put_item(Item=updated.model_dump(mode="json"))
        return updated

    def delete(self, task_id: str) -> bool:
        resp = self._table.delete_item(Key={"task_id": task_id}, ReturnValues="ALL_OLD")
        return "Attributes" in resp

    def ping(self) -> bool:
        self._client.describe_table(TableName=self._table_name)
        return True


def get_repository() -> TaskRepository:
    table = os.getenv("DYNAMODB_TABLE")
    if table:
        return DynamoDBRepository(table, os.getenv("AWS_REGION"))
    return InMemoryRepository()
