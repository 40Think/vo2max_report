from __future__ import annotations

from dataclasses import dataclass

from vo2max.domain import Client, Measurement
from vo2max.services.repository import InMemoryRepository


@dataclass(slots=True)
class ClientProfile:
    client: Client
    measurements: list[Measurement]


class ClientService:
    PROTECTED_FIELDS = {"id"}

    def __init__(self, repository: InMemoryRepository):
        self.repository = repository

    def create_client(
        self,
        first_name: str,
        last_name: str,
        second_name: str = "",
        **extra_fields,
    ) -> Client:
        client = Client(
            first_name=first_name.strip(),
            last_name=last_name.strip(),
            second_name=second_name.strip(),
            **extra_fields,
        )
        return self.repository.add_client(client)

    def update_client(self, client_id: str, **changes) -> Client:
        client = self.repository.get_client(client_id)
        for field_name, value in changes.items():
            if field_name in self.PROTECTED_FIELDS:
                raise ValueError(f"Client field cannot be changed: {field_name}")
            if not hasattr(client, field_name):
                raise ValueError(f"Unknown client field: {field_name}")
            setattr(client, field_name, value)
        self.repository.persist()
        return client

    def search_clients(self, query: str = "") -> list[Client]:
        clients = self.repository.list_clients()
        needle = query.strip().lower()
        if not needle:
            return clients
        return [
            client
            for client in clients
            if needle in client.full_name.lower()
            or needle in client.phone.lower()
            or needle in client.email.lower()
        ]

    def get_profile(self, client_id: str) -> ClientProfile:
        return ClientProfile(
            client=self.repository.get_client(client_id),
            measurements=self.repository.list_measurements_for_client(client_id),
        )
