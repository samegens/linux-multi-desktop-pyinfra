"""Unit tests for vault.py. Hermetic: never touches the real ~/Dropbox/ansible/.vault_pass."""

import os
import unittest
from pathlib import Path
from unittest import mock

import privy

import vault


class TestVaultPasswordResolution(unittest.TestCase):
    def setUp(self):
        self._env_patch = mock.patch.dict(os.environ, {}, clear=False)
        self._env_patch.start()
        os.environ.pop(vault.VAULT_PASSWORD_ENV_VAR, None)
        self.addCleanup(self._env_patch.stop)

    def test_env_var_takes_priority_over_file(self):
        os.environ[vault.VAULT_PASSWORD_ENV_VAR] = "from-env"
        with mock.patch.object(vault, "VAULT_PASSWORD_FILE", Path("/nonexistent/.vault_pass")):
            self.assertEqual(vault.vault_password(), "from-env")

    def test_falls_back_to_file_when_env_var_unset(self):
        with mock.patch.object(Path, "exists", return_value=True), mock.patch.object(
            Path, "read_text", return_value="from-file\n"
        ):
            self.assertEqual(vault.vault_password(), "from-file")

    def test_raises_when_neither_env_var_nor_file_available(self):
        with mock.patch.object(vault, "VAULT_PASSWORD_FILE", Path("/nonexistent/.vault_pass")):
            with self.assertRaises(RuntimeError):
                vault.vault_password()


class TestReveal(unittest.TestCase):
    def test_round_trips_a_privy_hidden_value(self):
        password = "test-password"
        hidden = privy.hide(b"super-secret-value", password)
        with mock.patch.dict(os.environ, {vault.VAULT_PASSWORD_ENV_VAR: password}):
            self.assertEqual(vault.reveal(hidden), b"super-secret-value")


if __name__ == "__main__":
    unittest.main()
