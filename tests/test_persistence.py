import json
import os
import tempfile
import unittest
from unittest.mock import patch

from core.config import ConfigManager
from core.history import HistoryManager


class PersistenceTests(unittest.TestCase):
    def test_config_save_is_atomic_and_invalid_fragment_count_uses_default(self):
        with tempfile.TemporaryDirectory() as data_dir:
            config_path = os.path.join(data_dir, "config.json")
            with open(config_path, "w", encoding="utf-8") as config_file:
                json.dump({"concurrent_fragments": "invalid"}, config_file)

            with patch("core.config.get_data_dir", return_value=data_dir):
                manager = ConfigManager()
                self.assertEqual(manager.get("concurrent_fragments"), 4)
                manager.set("proxy", "http://127.0.0.1:8080")

            with open(config_path, "r", encoding="utf-8") as config_file:
                saved = json.load(config_file)
            self.assertEqual(saved["proxy"], "http://127.0.0.1:8080")
            self.assertFalse(os.path.exists(config_path + ".tmp"))

    def test_history_save_is_atomic_and_ids_are_unique(self):
        with tempfile.TemporaryDirectory() as data_dir:
            with patch("core.history.get_data_dir", return_value=data_dir):
                history = HistoryManager()
                first = history.add("First", "https://example.com/1", None, "mp4")
                second = history.add("Second", "https://example.com/2", None, "mp4")

            self.assertNotEqual(first["id"], second["id"])
            self.assertTrue(os.path.isfile(history.history_file))
            self.assertFalse(os.path.exists(history.history_file + ".tmp"))


if __name__ == "__main__":
    unittest.main()
