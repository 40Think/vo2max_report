from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from vo2max.domain import Client
from vo2max.services import ClientService, FileRepository


class RepositoryPersistenceTest(unittest.TestCase):
    def test_file_repository_persists_clients_between_instances(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            state_path = Path(tmp_dir) / "state.pkl"
            first_repository = FileRepository(state_path=state_path)
            client = ClientService(first_repository).create_client(
                first_name="Stored",
                last_name="Client",
            )

            second_repository = FileRepository(state_path=state_path)

        self.assertEqual(second_repository.get_client(client.id).full_name, "Client Stored")


if __name__ == "__main__":
    unittest.main()
