"""
Tests for the prefab library.

No Blender modules are needed here — prefab_library.py is pure Python.
"""

import os
import tempfile

import pytest

from src.prefabs.prefab_library import (
    _REGISTRY,
    PrefabEntry,
    get_all_names,
    get_by_category,
    get_download_instructions,
    get_prefab,
    get_prefab_path,
    is_prefab_downloaded,
)

# ---------------------------------------------------------------------------
# Registry contents
# ---------------------------------------------------------------------------

class TestRegistry:
    def test_registry_is_non_empty(self):
        assert len(_REGISTRY) > 0

    def test_all_names_returns_sorted_list(self):
        names = get_all_names()
        assert names == sorted(names)

    def test_all_names_matches_registry_keys(self):
        assert set(get_all_names()) == set(_REGISTRY)

    def test_all_entries_have_valid_body_type(self):
        valid_body_types = {'blob', 'quadruped', 'humanoid'}
        for name, entry in _REGISTRY.items():
            assert entry.body_type in valid_body_types, (
                f"{name}: unexpected body_type {entry.body_type!r}"
            )

    def test_all_entries_have_valid_category(self):
        valid_categories = {'slime', 'creature', 'boss', 'prop'}
        for name, entry in _REGISTRY.items():
            assert entry.category in valid_categories, (
                f"{name}: unexpected category {entry.category!r}"
            )

    def test_all_entries_have_non_empty_source_url(self):
        for name, entry in _REGISTRY.items():
            assert entry.source_url.startswith('http'), (
                f"{name}: source_url should be a URL"
            )

    def test_all_entries_have_non_empty_creator(self):
        for name, entry in _REGISTRY.items():
            assert entry.creator, f"{name}: creator is empty"

    def test_all_entries_have_non_empty_description(self):
        for name, entry in _REGISTRY.items():
            assert entry.description, f"{name}: description is empty"

    def test_entry_name_matches_registry_key(self):
        for key, entry in _REGISTRY.items():
            assert entry.name == key, (
                f"Registry key {key!r} doesn't match entry name {entry.name!r}"
            )

    def test_slime_category_uses_blob_body_type(self):
        for entry in get_by_category('slime'):
            assert entry.body_type == 'blob', (
                f"{entry.name}: slime category should use blob body type"
            )

    def test_at_least_one_slime_registered(self):
        assert len(get_by_category('slime')) >= 1

    def test_at_least_one_creature_registered(self):
        assert len(get_by_category('creature')) >= 1

    def test_at_least_one_boss_registered(self):
        assert len(get_by_category('boss')) >= 1


# ---------------------------------------------------------------------------
# PrefabEntry immutability
# ---------------------------------------------------------------------------

class TestPrefabEntryImmutability:
    def test_entry_is_frozen(self):
        entry = get_prefab('simple_slime')
        with pytest.raises((AttributeError, TypeError)):
            entry.name = 'something_else'  # type: ignore[misc]


# ---------------------------------------------------------------------------
# get_prefab()
# ---------------------------------------------------------------------------

class TestGetPrefab:
    def test_returns_correct_entry(self):
        entry = get_prefab('simple_slime')
        assert entry.name == 'simple_slime'
        assert entry.category == 'slime'
        assert entry.body_type == 'blob'

    def test_raises_key_error_for_unknown_name(self):
        with pytest.raises(KeyError, match='not_a_real_prefab'):
            get_prefab('not_a_real_prefab')

    def test_error_message_includes_available_names(self):
        with pytest.raises(KeyError) as exc_info:
            get_prefab('mystery_model')
        assert 'Available' in str(exc_info.value)

    def test_ditch_dog_is_quadruped(self):
        entry = get_prefab('ditch_dog')
        assert entry.body_type == 'quadruped'

    def test_orb_weaver_siren_is_humanoid(self):
        entry = get_prefab('orb_weaver_siren')
        assert entry.body_type == 'humanoid'

    def test_boss_entries_exist(self):
        bosses = get_by_category('boss')
        boss_names = {e.name for e in bosses}
        assert 'pale_blight_queen' in boss_names
        assert 'orb_weaver_siren' in boss_names


# ---------------------------------------------------------------------------
# get_by_category()
# ---------------------------------------------------------------------------

class TestGetByCategory:
    def test_empty_list_for_unknown_category(self):
        assert get_by_category('nonexistent_category') == []

    def test_returns_list_of_prefab_entries(self):
        results = get_by_category('slime')
        assert all(isinstance(e, PrefabEntry) for e in results)

    def test_all_results_share_requested_category(self):
        for category in ('slime', 'creature', 'boss'):
            for entry in get_by_category(category):
                assert entry.category == category


# ---------------------------------------------------------------------------
# is_prefab_downloaded() and get_prefab_path()
# ---------------------------------------------------------------------------

class TestPrefabDownloadChecks:
    def test_not_downloaded_when_file_missing(self):
        assert not is_prefab_downloaded('simple_slime', prefabs_dir='/tmp/nonexistent_dir_xyz')

    def test_not_downloaded_for_unknown_prefab(self):
        assert not is_prefab_downloaded('ghost_model', prefabs_dir='/tmp')

    def test_get_prefab_path_raises_file_not_found_when_missing(self):
        with pytest.raises(FileNotFoundError):
            get_prefab_path('simple_slime', prefabs_dir='/tmp/nonexistent_dir_xyz')

    def test_get_prefab_path_raises_key_error_for_unknown_name(self):
        with pytest.raises(KeyError):
            get_prefab_path('ghost_model')

    def test_is_downloaded_true_when_glb_exists(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            prefab = get_prefab('simple_slime')
            glb_path = os.path.join(tmpdir, f"{prefab.filename}.glb")
            open(glb_path, 'w').close()  # create empty file
            assert is_prefab_downloaded('simple_slime', prefabs_dir=tmpdir)

    def test_is_downloaded_true_when_fbx_exists(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            prefab = get_prefab('ditch_dog')
            fbx_path = os.path.join(tmpdir, f"{prefab.filename}.fbx")
            open(fbx_path, 'w').close()
            assert is_prefab_downloaded('ditch_dog', prefabs_dir=tmpdir)

    def test_get_prefab_path_returns_correct_path_when_file_exists(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            prefab = get_prefab('mantis')
            glb_path = os.path.join(tmpdir, f"{prefab.filename}.glb")
            open(glb_path, 'w').close()
            result = get_prefab_path('mantis', prefabs_dir=tmpdir)
            assert result == glb_path


# ---------------------------------------------------------------------------
# get_download_instructions()
# ---------------------------------------------------------------------------

class TestGetDownloadInstructions:
    def test_returns_non_empty_string(self):
        instructions = get_download_instructions('simple_slime')
        assert isinstance(instructions, str)
        assert len(instructions) > 0

    def test_contains_source_url(self):
        entry = get_prefab('ditch_dog')
        instructions = get_download_instructions('ditch_dog')
        assert entry.source_url in instructions

    def test_contains_prefab_name(self):
        instructions = get_download_instructions('mantis')
        assert 'mantis' in instructions

    def test_contains_creator(self):
        entry = get_prefab('orb_weaver_siren')
        instructions = get_download_instructions('orb_weaver_siren')
        assert entry.creator in instructions

    def test_raises_key_error_for_unknown_name(self):
        with pytest.raises(KeyError):
            get_download_instructions('fake_prefab')
