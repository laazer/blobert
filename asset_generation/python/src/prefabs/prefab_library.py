"""
Prefab library — registry of downloadable Sketchfab models
that can replace procedural geometry in the generation pipeline.

To use a prefab, download it from its source URL and place the file
in the prefabs/ directory using the name: <prefab_name>.<ext>
(e.g. prefabs/simple_slime.glb).
"""

import os
from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class PrefabEntry:
    """Immutable descriptor for a single registered prefab model."""
    name: str
    filename: str
    category: str       # 'slime' | 'creature' | 'boss' | 'prop'
    body_type: str      # 'blob' | 'quadruped' | 'humanoid'
    description: str
    source_url: str
    creator: str


_REGISTRY: Dict[str, PrefabEntry] = {
    'simple_slime': PrefabEntry(
        name='simple_slime',
        filename='simple_slime',
        category='slime',
        body_type='blob',
        description='Minimal clean geometry slime — good baseline shape reference',
        source_url='https://sketchfab.com/3d-models/simple-slime-creature',
        creator='BlaizeJ',
    ),
    'ice_cream_slime': PrefabEntry(
        name='ice_cream_slime',
        filename='ice_cream_slime',
        category='slime',
        body_type='blob',
        description='Animated colorful slime variants (ice cream themed)',
        source_url='https://sketchfab.com/3d-models/ice-cream-slimes-set-free',
        creator='Empsy',
    ),
    'rimuru_slime': PrefabEntry(
        name='rimuru_slime',
        filename='rimuru_slime',
        category='slime',
        body_type='blob',
        description='Character-style slime with expressive face',
        source_url='https://sketchfab.com/3d-models/rimuru-slime',
        creator='tommdraws',
    ),
    'slime_1': PrefabEntry(
        name='slime_1',
        filename='slime_1',
        category='slime',
        body_type='blob',
        description='Animated slime variant 1 by dennish2010',
        source_url='https://sketchfab.com/3d-models/slime-1',
        creator='dennish2010',
    ),
    'mantis': PrefabEntry(
        name='mantis',
        filename='mantis',
        category='creature',
        body_type='quadruped',
        description='Insectoid creature — relevant to adhesion_bug style',
        source_url='https://sketchfab.com/3d-models/mantis-downloadable',
        creator='andrey.',
    ),
    'ditch_dog': PrefabEntry(
        name='ditch_dog',
        filename='ditch_dog',
        category='creature',
        body_type='quadruped',
        description='Rigged and animated quadruped — good quadruped animation reference',
        source_url='https://sketchfab.com/3d-models/ditch-dog-rigged-and-animated',
        creator='HighPolyDensity',
    ),
    'pale_blight_queen': PrefabEntry(
        name='pale_blight_queen',
        filename='pale_blight_queen',
        category='boss',
        body_type='quadruped',
        description='Boss-tier insectoid queen silhouette',
        source_url='https://sketchfab.com/3d-models/pale-blight-queen',
        creator='HighPolyDensity',
    ),
    'orb_weaver_siren': PrefabEntry(
        name='orb_weaver_siren',
        filename='orb_weaver_siren',
        category='boss',
        body_type='humanoid',
        description='Boss-tier humanoid siren variant',
        source_url='https://sketchfab.com/3d-models/orb-weaver-siren',
        creator='HighPolyDensity',
    ),
    'mobile_zombie': PrefabEntry(
        name='mobile_zombie',
        filename='mobile_zombie',
        category='creature',
        body_type='humanoid',
        description='Mobile game low-poly zombie — enemy art direction reference',
        source_url='https://sketchfab.com/3d-models/mobile-game-low-poly-zombie-pack',
        creator='huseyin.dogan',
    ),
}

_SUPPORTED_EXTENSIONS = ('.glb', '.gltf', '.fbx', '.obj', '.dae', '.blend')


def get_prefab(name: str) -> PrefabEntry:
    """Return the PrefabEntry for the given name.

    Raises:
        KeyError: if name is not registered.
    """
    if name not in _REGISTRY:
        available = ', '.join(sorted(_REGISTRY))
        raise KeyError(
            f"Unknown prefab: {name!r}. Available: {available}"
        )
    return _REGISTRY[name]


def get_prefab_path(name: str, prefabs_dir: str = 'prefabs') -> str:
    """Return the filesystem path to the downloaded prefab file.

    Searches for any supported extension in prefabs_dir.

    Raises:
        KeyError: if name is not registered.
        FileNotFoundError: if no matching file exists on disk.
    """
    entry = get_prefab(name)
    for ext in _SUPPORTED_EXTENSIONS:
        candidate = os.path.join(prefabs_dir, f"{entry.filename}{ext}")
        if os.path.exists(candidate):
            return candidate
    raise FileNotFoundError(
        f"Prefab '{name}' is not downloaded. "
        f"Expected a file named '{entry.filename}<ext>' in '{prefabs_dir}/'. "
        f"Download it from: {entry.source_url}"
    )


def is_prefab_downloaded(name: str, prefabs_dir: str = 'prefabs') -> bool:
    """Return True if the prefab file exists on disk."""
    try:
        get_prefab_path(name, prefabs_dir)
        return True
    except (KeyError, FileNotFoundError):
        return False


def get_all_names() -> List[str]:
    """Return all registered prefab names in sorted order."""
    return sorted(_REGISTRY)


def get_by_category(category: str) -> List[PrefabEntry]:
    """Return all prefabs belonging to the given category."""
    return [entry for entry in _REGISTRY.values() if entry.category == category]


def get_download_instructions(name: str) -> str:
    """Return human-readable download instructions for the given prefab."""
    entry = get_prefab(name)
    return (
        f"To use the '{name}' prefab:\n"
        f"  1. Open: {entry.source_url}\n"
        f"  2. Download the model (GLB or FBX format recommended)\n"
        f"  3. Rename the file to: {entry.filename}.glb  (or .fbx etc.)\n"
        f"  4. Place it in the prefabs/ directory\n"
        f"  5. Run generation with: --prefab {name}\n"
        f"\n"
        f"  Creator: {entry.creator}  |  Category: {entry.category}  |  Body type: {entry.body_type}\n"
        f"  {entry.description}"
    )
