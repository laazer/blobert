"""Animated enemy package: registry builder and concrete enemy classes."""

from src.enemies.animated.registry import AnimatedEnemyBuilder
from src.enemies.animated_carapace_husk import AnimatedCarapaceHusk
from src.enemies.animated_claw_crawler import AnimatedClawCrawler
from src.enemies.animated_imp import AnimatedImp
from src.enemies.animated_slug import AnimatedSlug
from src.enemies.animated_spider import AnimatedSpider
from src.enemies.animated_spitter import AnimatedSpitter

__all__ = [
    'AnimatedEnemyBuilder',
    'AnimatedSpitter',
    'AnimatedSpider',
    'AnimatedCarapaceHusk',
    'AnimatedClawCrawler',
    'AnimatedImp',
    'AnimatedSlug',
]
