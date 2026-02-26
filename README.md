# Symbolic Roguelike (Pygame)

Roguelike top-down minimalista con memoria persistente entre runs, perfil psicológico y puertas simbólicas.

## How to run

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m game.main
```

## Design architecture

```text
game/
├── main.py
├── config.py
├── core/
│   ├── game_manager.py
│   ├── state_machine.py
│   └── tension_system.py
├── systems/
│   ├── world_memory.py
│   ├── psychological_profile.py
│   ├── door_system.py
│   └── mirror_mode.py
├── entities/
│   ├── player.py
│   ├── enemy.py
│   ├── reflection.py
│   └── boss.py
├── ui/
│   ├── hud.py
│   └── menus.py
└── data/
    └── world_memory.json
```

### Responsibility split

- `main.py`: bootstrap de Pygame y loop delegado a `GameManager`.
- `config.py`: constantes globales (FPS, resolución, paleta, paths).
- `GameManager`: flujo de niveles, transiciones de estado, orquestación de sistemas.
- `StateMachine`: controla estados `MENU`, `RUNNING`, `BOSS`, `FINAL`, `GAME_OVER`.
- `TensionSystem`: calcula `tension_level` según conducta del jugador.
- `WorldMemory`: persistencia invisible de runs y buffer de acciones.
- `PsychologicalProfile`: puntajes de agresión/control/evasión y evaluación final.
- `DoorSystem`: puertas simbólicas y efectos en dificultad/progresión.
- `MirrorMode`: adapta Reflection con historial de acciones.
- `entities/`: dominio jugable (player/enemy/reflection/boss).
- `ui/`: HUD y menús desacoplados de la lógica de simulación.


## New controls

- `P`: pause/options menu
- `Right Click`: secondary burst skill
- `Shift`: dash
- `1/2/3`: pick level-up card


## Dramatic updates

- Symbolic doors now include iconography and dramatic narrative lines (`⚔`, `☾`, `🜏`, `✦`).
- Floating damage numbers appear for enemy and player damage.
- Enemy roster now includes size/behavior variants (`chaser`, `rusher`, `tank`).
- Boss archetype adapts to your build (duelist / colossus / oracle / overlord).
