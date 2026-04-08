"""Bone naming constants for enemy armatures (shared across body families)."""

from typing import List


class BoneNames:
    """Bone naming constants for armatures"""

    ROOT = "root"
    SPINE = "spine"
    HEAD = "head"
    BODY = "body"

    ARM_LEFT = "arm_l"
    ARM_RIGHT = "arm_r"
    LEG_LEFT = "leg_l"
    LEG_RIGHT = "leg_r"

    LEG_FRONT_LEFT = "leg_fl"
    LEG_FRONT_RIGHT = "leg_fr"
    LEG_MIDDLE_LEFT = "leg_ml"
    LEG_MIDDLE_RIGHT = "leg_mr"
    LEG_BACK_LEFT = "leg_bl"
    LEG_BACK_RIGHT = "leg_br"

    @classmethod
    def get_all_legs(cls) -> List[str]:
        return [
            cls.LEG_FRONT_LEFT,
            cls.LEG_FRONT_RIGHT,
            cls.LEG_MIDDLE_LEFT,
            cls.LEG_MIDDLE_RIGHT,
            cls.LEG_BACK_LEFT,
            cls.LEG_BACK_RIGHT,
            cls.LEG_LEFT,
            cls.LEG_RIGHT,
        ]

    @classmethod
    def get_quadruped_legs(cls) -> List[str]:
        return [
            cls.LEG_FRONT_LEFT,
            cls.LEG_FRONT_RIGHT,
            cls.LEG_MIDDLE_LEFT,
            cls.LEG_MIDDLE_RIGHT,
            cls.LEG_BACK_LEFT,
            cls.LEG_BACK_RIGHT,
        ]

    @classmethod
    def get_humanoid_arms(cls) -> List[str]:
        return [cls.ARM_LEFT, cls.ARM_RIGHT]

    @classmethod
    def get_humanoid_legs(cls) -> List[str]:
        return [cls.LEG_LEFT, cls.LEG_RIGHT]

    @classmethod
    def get_spider_leg_roots(cls) -> List[str]:
        return [f"leg_{i}" for i in range(8)]

    @classmethod
    def get_spider_leg_chain(cls, idx: int) -> List[str]:
        base = f"leg_{idx}"
        return [base, f"{base}_1", f"{base}_2"]

    @classmethod
    def get_spider_group_a_roots(cls) -> List[str]:
        return [f"leg_{i}" for i in (0, 2, 4, 6)]

    @classmethod
    def get_spider_group_b_roots(cls) -> List[str]:
        return [f"leg_{i}" for i in (1, 3, 5, 7)]
