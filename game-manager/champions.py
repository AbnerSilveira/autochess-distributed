import random

CHAMPIONS = [
    {"id": "warrior",   "name": "Guerreiro",  "hp": 120, "atk": 25, "def": 15, "skill": "Golpe Brutal"},
    {"id": "mage",      "name": "Mago",       "hp": 80,  "atk": 40, "def": 5,  "skill": "Bola de Fogo"},
    {"id": "archer",    "name": "Arqueiro",   "hp": 90,  "atk": 30, "def": 8,  "skill": "Flecha Perfurante"},
    {"id": "tank",      "name": "Tanque",     "hp": 160, "atk": 15, "def": 25, "skill": "Escudo Divino"},
    {"id": "healer",    "name": "Curandeiro", "hp": 100, "atk": 10, "def": 10, "skill": "Cura Sagrada"},
    {"id": "assassin",  "name": "Assassino",  "hp": 70,  "atk": 45, "def": 3,  "skill": "Golpe Critico"},
    {"id": "paladin",   "name": "Paladino",   "hp": 130, "atk": 20, "def": 20, "skill": "Julgamento"},
    {"id": "necro",     "name": "Necromante", "hp": 85,  "atk": 35, "def": 6,  "skill": "Drenar Vida"},
    {"id": "druid",     "name": "Druida",     "hp": 110, "atk": 22, "def": 12, "skill": "Furia da Natureza"},
    {"id": "berserker", "name": "Berserker",  "hp": 100, "atk": 50, "def": 2,  "skill": "Furia Sanguinaria"},
]

def generate_fallback_opponent(team_size, player_team=None):
    """
    Gera um oponente local quando o servico Matchmaking esta indisponivel.
    Tenta gerar um time diferente do player quando possivel.
    """
    available = [c["id"] for c in CHAMPIONS]

    if player_team:
        pool = [c for c in available if c not in player_team]
        if len(pool) < team_size:
            pool = available
    else:
        pool = available

    return random.sample(pool, min(team_size, len(pool)))