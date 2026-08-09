"""Unit tests for keyfile.py's set_key_value operation.

Testable by patching the `host` name keyfile.py imports (not pyinfra's real `host` proxy
directly - that's a protected object, pyinfra.context raises TypeError on any attempt to
patch/assign its attributes), same technique as test_archives.py.
"""

import unittest
from unittest import mock

import keyfile
from keyfile import set_key_value
from pyinfra.facts.files import FindInFile

class TestSetKeyValue(unittest.TestCase):
    def test_noops_and_yields_nothing_when_key_already_set_to_desired_value(self):
        # Arrange
        mock_host = mock.MagicMock()
        mock_host.get_fact.return_value = ["opencl=FALSE"]
        self._patch_host(mock_host)

        # Act
        commands: list[object] = list(
            set_key_value._inner( # pyright: ignore[reportUnknownMemberType, reportPrivateUsage, reportUnknownArgumentType]
                path="/home/user/.config/darktablerc", key="opencl", value="FALSE"
            )
        )

        # Assert
        self.assertEqual(commands, [])
        mock_host.get_fact.assert_called_once_with(FindInFile, path="/home/user/.config/darktablerc", pattern="^opencl=")
        mock_host.noop.assert_called_once()

    def test_appends_the_line_when_key_is_missing(self):
        # Arrange
        mock_host = mock.MagicMock()
        mock_host.get_fact.return_value = None
        self._patch_host(mock_host)

        # Act
        raw_commands: list[object] = list(
            set_key_value._inner( # pyright: ignore[reportUnknownMemberType, reportPrivateUsage, reportUnknownArgumentType]
                path="/home/user/.config/darktablerc", key="opencl", value="FALSE"
            )
        )
        commands = [str(c) for c in raw_commands]

        # Assert
        self.assertEqual(commands, ["echo opencl=FALSE >> /home/user/.config/darktablerc"])
        mock_host.noop.assert_not_called()

    def test_replaces_the_line_in_place_when_key_has_a_different_value(self):
        # Arrange
        mock_host = mock.MagicMock()
        mock_host.get_fact.return_value = ["opencl=TRUE"]
        self._patch_host(mock_host)

        # Act
        raw_commands: list[object] = list(
            set_key_value._inner( # pyright: ignore[reportUnknownMemberType, reportPrivateUsage, reportUnknownArgumentType]
                path="/home/user/.config/darktablerc", key="opencl", value="FALSE"
            )
        )
        commands = [str(c) for c in raw_commands]

        # Assert
        self.assertEqual(
            commands,
            ["sed -i 's/^opencl=.*/opencl=FALSE/' /home/user/.config/darktablerc"],
        )
        mock_host.noop.assert_not_called()

    def test_escapes_regex_and_sed_special_characters_in_key_and_value(self):
        # Arrange
        mock_host = mock.MagicMock()
        mock_host.get_fact.return_value = ["plugins/darkroom/def_path=old/value"]
        self._patch_host(mock_host)

        # Act
        raw_commands: list[object] = list(
            set_key_value._inner( # pyright: ignore[reportUnknownMemberType, reportPrivateUsage, reportUnknownArgumentType]
                path="/home/user/.config/darktablerc",
                key="plugins/darkroom/def_path",
                value="new/value",
            )
        )
        commands = [str(c) for c in raw_commands]

        # Assert
        mock_host.get_fact.assert_called_once_with(
            FindInFile,
            path="/home/user/.config/darktablerc",
            pattern=r"^plugins\/darkroom\/def_path=",
        )
        self.assertEqual(
            commands,
            [
                r"sed -i 's/^plugins\/darkroom\/def_path=.*/plugins\/darkroom\/def_path=new\/value/' "
                "/home/user/.config/darktablerc"
            ],
        )

    def _patch_host(self, mock_host: mock.MagicMock):
        patcher = mock.patch.object(keyfile, "host", mock_host)
        patcher.start()
        self.addCleanup(patcher.stop)

if __name__ == "__main__":
    unittest.main()
