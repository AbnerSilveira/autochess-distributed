import random

CHAMPION_POOL = [
    "warrior", "mage", "archer", "tank", "healer",
    "assassin", "paladin", "necro", "druid", "berserker"
]

def generate_opponent(team_size):
    """Gera time oponente aleatorio."""
    return random.sample(CHAMPION_POOL, min(team_size, len(CHAMPION_POOL)))