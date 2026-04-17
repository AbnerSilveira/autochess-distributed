from flask import Flask, request, jsonify
from combat import simulate_battle
import uuid
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("battle-engine")

# Armazena batalhas em memoria (para consulta posterior)
battles = {}

@app.route("/health")
def health():
    return jsonify({"status": "healthy", "service": "battle-engine"})

@app.route("/battle/simulate", methods=["POST"])
def simulate():
    data = request.get_json()

    # Validacao de entrada
    if not data or "player" not in data or "opponent" not in data:
        return jsonify({"error": "Campos player e opponent sao obrigatorios"}), 400

    result = simulate_battle(data["player"], data["opponent"])

    # Gera ID unico e armazena
    battle_id = f"battle_{uuid.uuid4().hex[:8]}"
    result["battle_id"] = battle_id
    battles[battle_id] = result

    logger.info(f"Batalha {battle_id}: vencedor={result['winner']}, turnos={result['rounds']}")
    return jsonify(result)

@app.route("/battle/result/<battle_id>")
def get_result(battle_id):
    if battle_id in battles:
        return jsonify(battles[battle_id])
    return jsonify({"error": "Batalha nao encontrada"}), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=True)