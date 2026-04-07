"""
Geometry builder for the player slime character

Anatomy:
  body      — squashed sphere, the main blob body
  drip      — smaller sphere blended into the base for a wet, drippy silhouette
  sclera ×2 — large white eye spheres, flattened front-to-back
  pupil  ×2 — dark spheres slightly in front of and inside the sclera
  highlight ×2 — tiny pure-white glint spheres offset up and to the side
  cheek  ×2 — soft pink blush marks on the sides of the face
  arm    ×2 — small sphere nubs sticking out from the body sides
"""

from ..core.blender_utils import apply_smooth_shading, create_sphere, join_objects
from ..materials.material_system import apply_material_to_object
from .player_materials import (
    SLIME_COLORS,
    create_cheek_material,
    create_highlight_material,
    create_pupil_material,
    create_sclera_material,
    create_slime_body_material,
)


class PlayerSlimeBody:
    """Builds and tracks all mesh parts that make up the player slime."""

    # Body dimensions (used by the armature builder too — must stay consistent)
    BODY_RADIUS_XY = 1.00
    BODY_RADIUS_Z = 0.80        # squashed — center at z=0.8, bottom z≈0, top z≈1.6

    # Eye geometry
    EYE_OFFSET_X = 0.34         # left/right separation
    EYE_OFFSET_Y = 0.84         # how far forward (Y-axis = front)
    EYE_OFFSET_Z = 1.05         # height of eye centre

    SCLERA_SCALE = (0.22, 0.12, 0.22)
    PUPIL_SCALE  = (0.13, 0.06, 0.13)
    HIGHLIGHT_SCALE = (0.05, 0.03, 0.05)
    HIGHLIGHT_DELTA = (0.07, 0.03, 0.08)  # offset from eye centre to glint position

    # Cheek geometry
    CHEEK_OFFSET_X = 0.62
    CHEEK_OFFSET_Y = 0.72
    CHEEK_OFFSET_Z = 0.90
    CHEEK_SCALE = (0.16, 0.06, 0.12)

    # Arm nub geometry
    ARM_OFFSET_X = 1.05
    ARM_OFFSET_Z = 0.85
    ARM_SCALE = (0.22, 0.18, 0.18)

    def __init__(self, color: str = "blue", rng=None, finish: str = "glossy", custom_color_hex: str = ""):
        self.color = color if color in SLIME_COLORS else "blue"
        self.rng = rng
        self.finish = finish
        self.custom_color_hex = custom_color_hex

        self._body_parts: list = []
        self._sclera_parts: list = []
        self._pupil_parts: list = []
        self._highlight_parts: list = []
        self._cheek_parts: list = []
        self._arm_parts: list = []

    # ------------------------------------------------------------------
    # Geometry creation
    # ------------------------------------------------------------------

    def create_body(self):
        """Main blob body — squashed sphere centered so bottom rests at z≈0."""
        body_z = self.BODY_RADIUS_Z  # center at same value as Z radius
        body = create_sphere(
            location=(0, 0, body_z),
            scale=(self.BODY_RADIUS_XY, self.BODY_RADIUS_XY, self.BODY_RADIUS_Z),
            subdivisions=2,
        )
        self._body_parts.append(body)

        # Drip — small sphere at the base for a wet, melting silhouette
        drip = create_sphere(
            location=(0, 0, 0.28),
            scale=(0.55, 0.55, 0.35),
            subdivisions=1,
        )
        self._body_parts.append(drip)

    def create_face(self):
        """Eyes (sclera + pupil + highlight) and cheeks."""
        self._create_eye(side=-1)   # left
        self._create_eye(side=1)    # right
        self._create_cheek(side=-1)
        self._create_cheek(side=1)

    def create_arms(self):
        """Two small sphere nubs that stick out from the body sides."""
        for side in (-1, 1):
            arm = create_sphere(
                location=(side * self.ARM_OFFSET_X, 0, self.ARM_OFFSET_Z),
                scale=self.ARM_SCALE,
            )
            self._arm_parts.append(arm)

    def apply_materials(self):
        """Apply themed materials to all parts."""
        body_mat      = create_slime_body_material(self.color, finish=self.finish, custom_color_hex=self.custom_color_hex)
        sclera_mat    = create_sclera_material()
        pupil_mat     = create_pupil_material()
        highlight_mat = create_highlight_material()
        cheek_mat     = create_cheek_material()

        for part in self._body_parts:
            apply_material_to_object(part, body_mat)
        for part in self._sclera_parts:
            apply_material_to_object(part, sclera_mat)
        for part in self._pupil_parts:
            apply_material_to_object(part, pupil_mat)
        for part in self._highlight_parts:
            apply_material_to_object(part, highlight_mat)
        for part in self._cheek_parts:
            apply_material_to_object(part, cheek_mat)
        for part in self._arm_parts:
            apply_material_to_object(part, body_mat)

    def finalize(self):
        """Join all parts into a single mesh and return it."""
        all_parts = (
            self._body_parts
            + self._sclera_parts
            + self._pupil_parts
            + self._highlight_parts
            + self._cheek_parts
            + self._arm_parts
        )
        mesh = join_objects(all_parts)
        apply_smooth_shading(mesh)
        return mesh

    def build(self):
        """Run the full build pipeline and return the combined mesh."""
        self.create_body()
        self.create_face()
        self.create_arms()
        self.apply_materials()
        return self.finalize()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _create_eye(self, side: int):
        """Create sclera + pupil + highlight for one eye. side = -1 (left) or 1 (right)."""
        x = side * self.EYE_OFFSET_X
        ey, ez = self.EYE_OFFSET_Y, self.EYE_OFFSET_Z

        sclera = create_sphere(
            location=(x, ey, ez),
            scale=self.SCLERA_SCALE,
        )
        self._sclera_parts.append(sclera)

        # Pupil sits slightly further forward (higher Y) and inside the sclera
        pupil = create_sphere(
            location=(x, ey + 0.06, ez),
            scale=self.PUPIL_SCALE,
        )
        self._pupil_parts.append(pupil)

        # Highlight — offset up and toward the centre for a lively glint
        dx, dy, dz = self.HIGHLIGHT_DELTA
        highlight = create_sphere(
            location=(x + (-side * dx), ey + dy, ez + dz),
            scale=self.HIGHLIGHT_SCALE,
        )
        self._highlight_parts.append(highlight)

    def _create_cheek(self, side: int):
        """Small blush mark just below and outside each eye. side = -1 (left) or 1."""
        cheek = create_sphere(
            location=(
                side * self.CHEEK_OFFSET_X,
                self.CHEEK_OFFSET_Y,
                self.CHEEK_OFFSET_Z,
            ),
            scale=self.CHEEK_SCALE,
        )
        self._cheek_parts.append(cheek)
