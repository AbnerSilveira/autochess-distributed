from flask import Flask, request, jsonify
from opponent_generator import generate_opponent
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("matchmaking")

# Fila simples de matchmaking (nao usada ativamente, apenas para status)
match_queue = []

@app.route("/health")
def health():
    return jsonify({"status": "healthy", "service": "matchmaking"})

@app.route("/match/find", methods=["POST"])
def find_match():
    data = request.get_json()
    team_size = data.get("team_size", 3)

    # Validacao de entrada
    if not isinstance(team_size, int) or team_size < 1 or team_size > 5:
        return jsonify({"error": "team_size deve ser entre 1 e 5"}), 400

    opponent = generate_opponent(team_size)
    logger.info(f"Oponente gerado: {opponent}")

    return jsonify({
        "opponent_team": opponent,
        "match_type": "bot",
        "difficulty": "normal"
    })

@app.route("/match/queue")
def queue_status():
    return jsonify({"queue_size": len(match_queue)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)