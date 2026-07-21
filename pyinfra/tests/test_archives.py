"""Unit tests for archives.py's download_and_extract operation.

Testable by patching the `host` name archives.py imports (not pyinfra's real `host` proxy
directly - that's a protected object, pyinfra.context raises TypeError on any attempt to
patch/assign its attributes) and, for the "do the work" path, by patching
files.download._inner() itself so the real download logic (which also reaches the real `host`
proxy) never runs - we're testing the tar/mkdir/rm commands this operation itself generates,
not files.download's own internals.
"""

import unittest
from unittest import mock

import archives
from archives import download_and_extract
from pyinfra.facts.files import File
from pyinfra.operations import files

class TestDownloadAndExtract(unittest.TestCase):
    def test_noops_and_yields_nothing_when_creates_path_already_exists(self):
        # Arrange
        mock_host = mock.MagicMock()
        mock_host.get_fact.return_value = True
        self._patch_host(mock_host)

        # Act
        commands: list[object] = list(
            download_and_extract._inner( # pyright: ignore[reportUnknownMemberType, reportPrivateUsage, reportUnknownArgumentType]
                url="https://example.com/thing.tar.gz",
                dest="/opt/thing",
                creates="/opt/thing/thing",
            )
        )

        # Assert
        self.assertEqual(commands, [])
        mock_host.get_fact.assert_called_once_with(File, path="/opt/thing/thing")
        mock_host.noop.assert_called_once()

    def test_generates_extract_commands_against_the_downloaded_archive_when_creates_path_is_missing(self):
        # Arrange
        mock_host = mock.MagicMock()
        mock_host.get_fact.return_value = None
        mock_host.get_temp_filename.return_value = "/tmp/pyinfra-abc123"
        self._patch_host(mock_host)

        def fake_download_inner(src: str, dest: str):
            yield f"FAKE_DOWNLOAD {src} -> {dest}"

        self._patch_download_inner(fake_download_inner)

        # Act
        raw_commands: list[object] = list(
            download_and_extract._inner( # pyright: ignore[reportUnknownMemberType, reportPrivateUsage, reportUnknownArgumentType]
                url="https://example.com/thing.tar.gz",
                dest="/opt/thing",
                creates="/opt/thing/thing",
            )
        )
        commands = [str(c) for c in raw_commands]

        # Assert
        self.assertEqual(
            commands,
            [
                "FAKE_DOWNLOAD https://example.com/thing.tar.gz -> /tmp/pyinfra-abc123",
                "mkdir -p /opt/thing",
                "tar -xzf /tmp/pyinfra-abc123 -C /opt/thing",
                "rm -f /tmp/pyinfra-abc123",
            ],
        )
        mock_host.noop.assert_not_called()

    def _patch_host(self, mock_host: mock.MagicMock):
        patcher = mock.patch.object(archives, "host", mock_host)
        patcher.start()
        self.addCleanup(patcher.stop)

    def _patch_download_inner(self, side_effect):
        patcher = mock.patch.object(files.download, "_inner", side_effect=side_effect)
        patcher.start()
        self.addCleanup(patcher.stop)

if __name__ == "__main__":
    unittest.main()
