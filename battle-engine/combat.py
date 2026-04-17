import random
import copy

CHAMPION_STATS = {
    "warrior":   {"hp": 120, "atk": 25, "def": 15, "skill": "Golpe Brutal"},
    "mage":      {"hp": 80,  "atk": 40, "def": 5,  "skill": "Bola de Fogo"},
    "archer":    {"hp": 90,  "atk": 30, "def": 8,  "skill": "Flecha Perfurante"},
    "tank":      {"hp": 160, "atk": 15, "def": 25, "skill": "Escudo Divino"},
    "healer":    {"hp": 100, "atk": 10, "def": 10, "skill": "Cura Sagrada"},
    "assassin":  {"hp": 70,  "atk": 45, "def": 3,  "skill": "Golpe Critico"},
    "paladin":   {"hp": 130, "atk": 20, "def": 20, "skill": "Julgamento"},
    "necro":     {"hp": 85,  "atk": 35, "def": 6,  "skill": "Drenar Vida"},
    "druid":     {"hp": 110, "atk": 22, "def": 12, "skill": "Furia da Natureza"},
    "berserker": {"hp": 100, "atk": 50, "def": 2,  "skill": "Furia Sanguinaria"},
}


def _build_team(champion_ids, side):
    """Monta um time com copias dos stats para nao afetar o dicionario original."""
    team = []
    for cid in champion_ids:
        stats = copy.deepcopy(CHAMPION_STATS.get(cid, CHAMPION_STATS["warrior"]))
        stats["id"] = cid
        stats["side"] = side
        team.append(stats)
    return team


def _plan_attack(attacker, defenders, turn):
    """
    Planeja um ataque sem aplicar o dano ainda.
    Retorna um dicionario com as informacoes do ataque.
    """
    if not defenders:
        return None

    target = random.choice(defenders)
    damage = max(1, attacker["atk"] - target["def"] + random.randint(-5, 5))
    used_skill = random.random() < 0.2
    if used_skill:
        damage *= 2

    attacker_tag = f"{attacker['id']}[{'P' if attacker['side'] == 'player' else 'O'}]"
    target_tag = f"{target['id']}[{'P' if target['side'] == 'player' else 'O'}]"

    if used_skill:
        action = f"{attacker_tag} usa {attacker['skill']} em {target_tag}"
    else:
        action = f"{attacker_tag} ataca {target_tag}"

    return {
        "turn": turn,
        "attacker_uid": id(attacker),   # referencia unica para linkar
        "target_uid": id(target),
        "target_ref": target,
        "damage": damage,
        "action": action,
        "used_skill": used_skill,
    }


def simulate_battle(player_ids, opponent_ids):
    """
    Simula batalha SIMULTANEA turno-a-turno.
    - Todos os campeoes vivos planejam seu ataque ao mesmo tempo
    - Todos os danos sao aplicados simultaneamente
    - Mortes sao resolvidas apos todos os ataques do turno

    Desempate apos 30 turnos:
    1. HP total do time restante
    2. HP do campeao com mais vida no time
    3. Player vence (ultimo recurso)
    """
    p_team = _build_team(player_ids, "player")
    o_team = _build_team(opponent_ids, "opponent")

    log = []
    turn = 0
    max_turns = 30

    while p_team and o_team and turn < max_turns:
        turn += 1

        # FASE 1: todos os vivos planejam ataques simultaneamente
        # (snapshots para garantir que todos atacam "ao mesmo tempo")
        planned = []
        for attacker in p_team:
            plan = _plan_attack(attacker, o_team, turn)
            if plan:
                planned.append(plan)
        for attacker in o_team:
            plan = _plan_attack(attacker, p_team, turn)
            if plan:
                planned.append(plan)

        # FASE 2: registra todas as acoes no log (marcadas como mesmo turno)
        for plan in planned:
            log.append({
                "turn": plan["turn"],
                "action": plan["action"],
                "damage": plan["damage"],
                "phase": "attack"
            })

        # FASE 3: aplica todos os danos simultaneamente
        for plan in planned:
            plan["target_ref"]["hp"] -= plan["damage"]

        # FASE 4: resolve mortes (campeoes com HP <= 0 sao removidos)
        dead_in_turn = []
        for champ in p_team + o_team:
            if champ["hp"] <= 0 and champ not in dead_in_turn:
                dead_in_turn.append(champ)

        for champ in dead_in_turn:
            tag = f"{champ['id']}[{'P' if champ['side'] == 'player' else 'O'}]"
            log.append({
                "turn": turn,
                "action": f"{tag} foi derrotado!",
                "damage": 0,
                "phase": "death"
            })
            if champ in p_team:
                p_team.remove(champ)
            elif champ in o_team:
                o_team.remove(champ)

    # DETERMINACAO DO VENCEDOR
    winner, tiebreak = _determine_winner(p_team, o_team, turn, max_turns)

    result = {"winner": winner, "log": log, "rounds": turn}
    if tiebreak:
        result["tiebreak"] = tiebreak

    return result


def _determine_winner(p_team, o_team, turn, max_turns):
    """
    Retorna (winner, tiebreak_reason).
    tiebreak_reason e None se nao houve empate a resolver.
    """
    # Caso 1: um time eliminado antes do limite
    if p_team and not o_team:
        return "player", None
    if o_team and not p_team:
        return "opponent", None

    # Caso 2: ambos eliminados no mesmo turno (simultaneamente)
    if not p_team and not o_team:
        # Empate duplo no mesmo turno — player vence por tiebreak final
        return "player", "ambos_eliminados_tiebreak_player"

    # Caso 3: atingiu 30 turnos com os dois times vivos
    # Desempate A: HP total
    p_total_hp = sum(c["hp"] for c in p_team)
    o_total_hp = sum(c["hp"] for c in o_team)

    if p_total_hp > o_total_hp:
        return "player", "hp_total"
    if o_total_hp > p_total_hp:
        return "opponent", "hp_total"

    # Desempate B: HP do campeao mais forte vivo
    p_max_hp = max(c["hp"] for c in p_team)
    o_max_hp = max(c["hp"] for c in o_team)

    if p_max_hp > o_max_hp:
        return "player", "hp_individual"
    if o_max_hp > p_max_hp:
        return "opponent", "hp_individual"

    # Tiebreak final: player vence
    return "player", "tiebreak_final"