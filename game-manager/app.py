from flask import Flask, request, jsonify
from resilience import create_resilient_session
from champions import CHAMPIONS, generate_fallback_opponent
import uuid
import random
import logging

app = Flask(__name__, static_folder="static", static_url_path="")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("game-manager")

# Estado em memoria
games = {}
idempotency_cache = {}

# Sessao HTTP com retry automatico
session = create_resilient_session()

# URLs dos outros servicos (nomes dos containers na rede Docker)
MATCHMAKING_URL = "http://matchmaking:5001"
BATTLE_ENGINE_URL = "http://battle-engine:5002"

@app.route("/")
def index():
    return app.send_static_file("index.html")

@app.route("/health")
def health():
    return jsonify({"status": "healthy", "service": "game-manager"})


@app.route("/champions")
def list_champions():
    return jsonify(CHAMPIONS)


@app.route("/game/start", methods=["POST"])
def start_game():
    data = request.get_json()

    if not data or "team" not in data:
        return jsonify({"error": "Campo team e obrigatorio"}), 400

    request_id = data.get("request_id")

    # IDEMPOTENCIA
    if request_id and request_id in idempotency_cache:
        logger.info(f"Idempotencia: retornando resultado em cache para {request_id}")
        return jsonify(idempotency_cache[request_id]), 200

    player_team = data["team"]
    player_id = data.get("player_id", f"player_{uuid.uuid4().hex[:6]}")

    # Valida campeoes
    valid_ids = [c["id"] for c in CHAMPIONS]
    for champ in player_team:
        if champ not in valid_ids:
            return jsonify({"error": f"Campeao invalido: {champ}"}), 400

    # Valida tamanho do time
    if len(player_team) < 1 or len(player_team) > 5:
        return jsonify({"error": "Time deve ter entre 1 e 5 campeoes"}), 400

    # Matchmaking (retry + fallback + timeout)
    opponent = find_opponent(player_team)

    # Battle Engine (retry + fallback + timeout)
    battle_result = run_battle(player_team, opponent)

    game_id = f"game_{uuid.uuid4().hex[:8]}"
    result = {
        "game_id": game_id,
        "player_id": player_id,
        "player_team": player_team,
        "opponent_team": opponent,
        "result": battle_result["winner"],
        "battle_log": battle_result["log"],
        "rounds": battle_result["rounds"]
    }

    games[game_id] = result

    if request_id:
        idempotency_cache[request_id] = result

    return jsonify(result), 200


def find_opponent(player_team):
    """Busca oponente via Matchmaking com RETRY + FALLBACK + TIMEOUT."""
    try:
        resp = session.post(
            f"{MATCHMAKING_URL}/match/find",
            json={"team_size": len(player_team)},
            timeout=(3, 5)
        )
        resp.raise_for_status()
        return resp.json()["opponent_team"]
    except Exception as e:
        logger.warning(f"Matchmaking falhou: {e}. Ativando fallback local.")
        return generate_fallback_opponent(len(player_team), player_team)


def run_battle(player_team, opponent_team):
    """Executa batalha via Battle Engine com RETRY + FALLBACK + TIMEOUT."""
    try:
        resp = session.post(
            f"{BATTLE_ENGINE_URL}/battle/simulate",
            json={"player": player_team, "opponent": opponent_team},
            timeout=(3, 10)
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.warning(f"Battle Engine falhou: {e}. Ativando fallback local.")
        winner = "player" if random.random() > 0.4 else "opponent"
        return {
            "winner": winner,
            "log": [{"turn": 1, "action": "Simulacao em modo fallback (servico indisponivel)"}],
            "rounds": 1
        }


@app.route("/game/status/<game_id>")
def game_status(game_id):
    if game_id in games:
        return jsonify(games[game_id])
    return jsonify({"error": "Partida nao encontrada"}), 404


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)