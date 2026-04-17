# AutoChess Distribuído

![Status](https://img.shields.io/badge/status-funcional-success)
![Docker](https://img.shields.io/badge/docker-3_containers-blue)
![Python](https://img.shields.io/badge/python-3.11-yellow)

Sistema distribuído com 3 microsserviços Docker implementando um jogo no estilo **AutoChess** (inspirado em Teamfight Tactics). O jogo é um **torneio Best-of-5** onde o jogador monta times estratégicos que batalham em combate simultâneo contra oponentes gerados pelo sistema.

Projeto desenvolvido para a avaliação N1-02 de **Sistemas Distribuídos**.

## 🎯 Objetivo

Demonstrar na prática os conceitos fundamentais de sistemas distribuídos através de uma aplicação funcional com interface visual, incluindo padrões de resiliência (retry, fallback, timeout), idempotência e isolamento de rede.

## 🏗️ Arquitetura

Três containers Docker comunicando-se via REST/HTTP em uma rede interna isolada (`autochess-net`):

| Serviço         | Porta | Responsabilidade                                     |
|-----------------|-------|------------------------------------------------------|
| Game Manager    | 5000  | Orquestrador, gerencia estado, serve a interface web |
| Matchmaking     | 5001  | Gera oponentes (interno à rede Docker)               |
| Battle Engine   | 5002  | Simula combate simultâneo turno-a-turno              |

Apenas o **Game Manager** expõe porta para o host. Os demais serviços são acessíveis somente pela rede interna Docker, funcionando como verdadeiros microsserviços isolados.

## ⚡ Conceitos Implementados

- **Retry**: tentativas automáticas com exponential backoff (0.5s, 1s, 2s) via `urllib3.Retry`
- **Fallback**: resposta alternativa local quando um serviço está indisponível
- **Timeout**: limite de tempo em cada chamada HTTP (connect + read separados)
- **Idempotência**: cache por `request_id` previne processamento duplicado
- **Health checks**: cada serviço expõe `/health` monitorado pelo Docker
- **Isolamento de rede**: apenas o gateway é acessível externamente
- **Orquestração**: `depends_on` com `service_healthy` garante ordem de boot correta

## 🎮 Como Funciona o Jogo

Um **torneio Best-of-5** (primeiro a vencer 3 rodadas ganha):

1. Jogador escolhe de 1 a 5 campeões do seu time
2. Sistema gera oponente aleatório via serviço de Matchmaking
3. Battle Engine simula combate **simultâneo** turno-a-turno
4. A cada rodada, jogador precisa **mudar a combinação** do time
5. Torneio termina quando alguém atingir 3 vitórias

### Combate Simultâneo
- Todos os campeões vivos atacam **ao mesmo tempo** em cada turno
- Dano é aplicado simultaneamente em todos os alvos
- Mortes são resolvidas após todos os ataques do turno
- Limite de 30 turnos por batalha
- **Desempate por HP total**, depois HP individual, depois bonificação ao jogador

### 10 Campeões Disponíveis

| Campeão    | HP  | ATK | DEF | Habilidade          | Papel                         |
|------------|-----|-----|-----|---------------------|-------------------------------|
| Guerreiro  | 120 | 25  | 15  | Golpe Brutal        | Dano físico equilibrado       |
| Mago       | 80  | 40  | 5   | Bola de Fogo        | Alto dano, frágil             |
| Arqueiro   | 90  | 30  | 8   | Flecha Perfurante   | Dano à distância              |
| Tanque     | 160 | 15  | 25  | Escudo Divino       | Absorve dano                  |
| Curandeiro | 100 | 10  | 10  | Cura Sagrada        | Suporte                       |
| Assassino  | 70  | 45  | 3   | Golpe Crítico       | Dano explosivo, muito frágil  |
| Paladino   | 130 | 20  | 20  | Julgamento          | Híbrido tanque/dano           |
| Necromante | 85  | 35  | 6   | Drenar Vida         | Dano mágico médio             |
| Druida     | 110 | 22  | 12  | Fúria da Natureza   | Suporte híbrido               |
| Berserker  | 100 | 50  | 2   | Fúria Sanguinária   | Dano extremo                  |

## 📋 Pré-requisitos

- Docker Desktop (Windows, macOS ou Linux)
- Docker Compose (incluso no Docker Desktop)
- Um navegador web moderno (Chrome, Firefox, Edge)

## 🚀 Como executar

```bash
# Clone o repositório
git clone 
cd autochess-distributed

# Suba os 3 containers
docker compose up --build

# Abra no navegador
# → http://localhost:5000
```

Para parar:

```bash
docker compose down
```

## 🧪 Testes

### Interface web
Abra http://localhost:5000 e jogue um torneio completo.

### Testes via API (curl)

```bash
# Health check
curl http://localhost:5000/health

# Listar campeões
curl http://localhost:5000/champions

# Iniciar uma partida (Windows PowerShell)
'{"player_id": "p1", "team": ["warrior", "mage", "archer"], "request_id": "req001"}' | Out-File -FilePath body.json -Encoding ascii
curl.exe -X POST http://localhost:5000/game/start -H "Content-Type: application/json" -d "@body.json"
```

### Teste de Resiliência — Fallback

Derrube um serviço e veja o sistema continuar funcionando:

```bash
# Para o matchmaking
docker compose stop matchmaking

# Faça uma partida — sistema ativa fallback local
curl.exe -X POST http://localhost:5000/game/start -H "Content-Type: application/json" -d "@body.json"

# Reinicie
docker compose start matchmaking
```

### Teste de Idempotência

Execute a mesma requisição com o mesmo `request_id` múltiplas vezes. O `game_id` retornado será **idêntico** (o resultado vem do cache, sem re-processar).

## 📁 Estrutura do Projeto
autochess-distributed/
├── docker-compose.yml           # Orquestração dos 3 containers
├── README.md                    # Este arquivo
├── DOCUMENTACAO.md              # Documentação completa do projeto
├── game-manager/                # Orquestrador (porta 5000)
│   ├── app.py
│   ├── champions.py
│   ├── resilience.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── static/
│       └── index.html           # Interface web (pixel art)
├── matchmaking/                 # Gerador de oponentes (porta 5001)
│   ├── app.py
│   ├── opponent_generator.py
│   ├── Dockerfile
│   └── requirements.txt
├── battle-engine/               # Motor de combate (porta 5002)
│   ├── app.py
│   ├── combat.py
│   ├── Dockerfile
│   └── requirements.txt
└── docs/                        # Diagramas de arquitetura
├── arquitetura.drawio
└── sequencia.drawio

## 🔌 Endpoints

### Game Manager (5000) — público
| Método | Rota                        | Descrição                    |
|--------|-----------------------------|------------------------------|
| GET    | `/`                         | Interface web                |
| GET    | `/health`                   | Status do serviço            |
| GET    | `/champions`                | Lista dos 10 campeões        |
| POST   | `/game/start`               | Inicia nova partida          |
| GET    | `/game/status/<game_id>`    | Consulta resultado de partida|

### Matchmaking (5001) — interno
| Método | Rota              | Descrição               |
|--------|-------------------|-------------------------|
| GET    | `/health`         | Status do serviço       |
| POST   | `/match/find`     | Gera oponente aleatório |
| GET    | `/match/queue`    | Status da fila          |

### Battle Engine (5002) — interno
| Método | Rota                           | Descrição          |
|--------|--------------------------------|--------------------|
| GET    | `/health`                      | Status do serviço  |
| POST   | `/battle/simulate`             | Simula combate     |
| GET    | `/battle/result/<battle_id>`   | Consulta resultado |

## 🛠️ Stack Tecnológica

- **Linguagem**: Python 3.11
- **Framework Web**: Flask 3.0
- **HTTP Client**: Requests + urllib3 (retry)
- **Containerização**: Docker + Docker Compose
- **Interface**: HTML + CSS + JavaScript vanilla + SVG pixel art
- **Fonte**: Press Start 2P (Google Fonts)

## 👥 Equipe

- [Seu Nome]
- Gabriel Forza
- Maria Clara

## 📚 Documentação adicional

Veja [DOCUMENTACAO.md](DOCUMENTACAO.md) para explicação técnica completa, incluindo arquitetura detalhada, fluxos de comunicação e guia passo a passo de instalação do zero.

## 📝 Licença

Projeto acadêmico — Sistemas Distribuídos N1-02 — 2026.