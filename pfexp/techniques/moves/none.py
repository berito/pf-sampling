"""No move step: particles are left as resampled (the standard particle filter)."""
from pfexp.registry import register
from pfexp.techniques.base import Move


@register("move", "none")
class NoMove(Move):
    def move(self, particles, context):
        return particles
