"""Unit tests for pkgmgr.py's package-name resolution. Pure logic, no pyinfra host context needed."""

import unittest
from unittest import mock

import pkgmgr
from pkgmgr import Distro, PackageManager, resolve_distro_from_os_release, resolve_package_names


class TestResolvePackageNames(unittest.TestCase):
    def test_passes_through_unchanged_when_no_overrides_defined_for_manager(self):
        # Arrange
        packages = ["git", "vim"]
        self._patch_overrides({})

        # Act
        resolved = resolve_package_names(PackageManager.APT, packages)

        # Assert
        self.assertEqual(resolved, ["git", "vim"])

    def test_passes_through_unchanged_when_overrides_dict_is_empty(self):
        # Arrange
        packages = ["git", "vim"]
        self._patch_overrides({PackageManager.APT: {}})

        # Act
        resolved = resolve_package_names(PackageManager.APT, packages)

        # Assert
        self.assertEqual(resolved, ["git", "vim"])

    def test_substitutes_only_the_overridden_name(self):
        # Arrange
        packages = ["fonts-powerline", "git"]
        self._patch_overrides({PackageManager.DNF: {"fonts-powerline": "powerline-fonts"}})

        # Act
        resolved = resolve_package_names(PackageManager.DNF, packages)

        # Assert
        self.assertEqual(resolved, ["powerline-fonts", "git"])

    def test_override_for_one_manager_does_not_leak_into_another(self):
        # Arrange
        packages = ["fonts-powerline"]
        self._patch_overrides({PackageManager.DNF: {"fonts-powerline": "powerline-fonts"}})

        # Act
        resolved = resolve_package_names(PackageManager.APT, packages)

        # Assert
        self.assertEqual(resolved, ["fonts-powerline"])

    def _patch_overrides(self, table: dict[PackageManager, dict[str, str]]):
        patcher = mock.patch.object(pkgmgr, "PACKAGE_NAME_OVERRIDES", table)
        patcher.start()
        self.addCleanup(patcher.stop)


class TestResolveDistroFromOsRelease(unittest.TestCase):
    def test_recognizes_linux_mint(self):
        # Arrange
        os_release = 'NAME="Linux Mint"\nID=linuxmint\nID_LIKE="ubuntu debian"\n'

        # Act
        distro = resolve_distro_from_os_release(os_release)

        # Assert
        self.assertEqual(distro, Distro.MINT)

    def test_recognizes_fedora(self):
        # Arrange
        os_release = 'NAME=Fedora\nID=fedora\nVERSION_ID=43\n'

        # Act
        distro = resolve_distro_from_os_release(os_release)

        # Assert
        self.assertEqual(distro, Distro.FEDORA)

    def test_recognizes_ubuntu(self):
        # Arrange
        os_release = 'NAME="Ubuntu"\nID=ubuntu\nVERSION_ID="24.04"\n'

        # Act
        distro = resolve_distro_from_os_release(os_release)

        # Assert
        self.assertEqual(distro, Distro.UBUNTU)

    def test_returns_none_for_unrecognized_id(self):
        # Arrange
        os_release = 'NAME="Arch Linux"\nID=arch\n'

        # Act
        distro = resolve_distro_from_os_release(os_release)

        # Assert
        self.assertIsNone(distro)

    def test_returns_none_when_id_field_is_missing(self):
        # Arrange
        os_release = 'NAME="Some OS"\nVERSION_ID=1\n'

        # Act
        distro = resolve_distro_from_os_release(os_release)

        # Assert
        self.assertIsNone(distro)


if __name__ == "__main__":
    unittest.main()
