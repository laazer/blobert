"""
Prefab loader — imports a registered prefab model into the active
Blender scene and returns it ready for use as a mesh base.
"""

from typing import Tuple

from .prefab_library import (
    PrefabEntry,
    get_prefab,
    get_prefab_path,
    is_prefab_downloaded,
)


def load_prefab_mesh(name: str, prefabs_dir: str = 'prefabs') -> Tuple:
    """Import a registered prefab model and return (mesh, entry).

    The prefab file must be downloaded and placed in prefabs_dir before
    calling this function. Use get_download_instructions(name) to see
    where to obtain it.

    Args:
        name: Registered prefab name (see prefab_library.get_all_names()).
        prefabs_dir: Directory containing downloaded prefab files.

    Returns:
        (mesh, entry) — the imported Blender mesh object and its PrefabEntry.

    Raises:
        KeyError: if name is not a registered prefab.
        FileNotFoundError: if the prefab file has not been downloaded.
        RuntimeError: if Blender fails to import the model.
    """
    entry: PrefabEntry = get_prefab(name)

    if not is_prefab_downloaded(name, prefabs_dir):
        from .prefab_library import get_download_instructions
        raise FileNotFoundError(
            f"Prefab '{name}' is not downloaded.\n\n"
            + get_download_instructions(name)
        )

    filepath = get_prefab_path(name, prefabs_dir)

    from ..integration.external_model_importer import ExternalModelImporter

    importer = ExternalModelImporter()
    importer.import_model(filepath, enemy_name=name)

    if importer.mesh is None:
        raise RuntimeError(
            f"Prefab '{name}' was imported but no mesh was found in the file."
        )

    return importer.mesh, entry


def load_prefab_mesh_if_requested(prefab_name: str | None):
    """Load a prefab mesh when ``prefab_name`` is set; otherwise return None."""
    if not prefab_name:
        return None
    print(f"📦 Loading prefab: {prefab_name}")
    mesh, entry = load_prefab_mesh(prefab_name)
    print(f"✅ Prefab loaded: {entry.description}")
    return mesh
