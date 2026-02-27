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


- Hidden ending removed: now all runs close with a clear spiritual archetype ending.
- Added **Omega Final Boss** on level 8 for a harder climax.
- Added 10+ new chaotic/varied shooting modes (fan, cross, chaos, spiral, sniper, rapid, etc.).
- Symbolic doors now include iconography and dramatic narrative lines (`⚔`, `☾`, `🜏`, `✦`).
- Floating damage numbers appear for enemy and player damage.
- Enemy roster now includes size/behavior variants (`chaser`, `rusher`, `tank`).
- Boss archetype adapts to your build (duelist / colossus / oracle / overlord).


## FAQ

- **¿Por qué tengo que hacer commit al cerrar el juego?**
  No deberías. El juego no exige commits. Los commits son parte del flujo del agente/desarrollo, no una mecánica del runtime.
- **¿Por qué no veía sonido?**
  Ahora el proyecto incluye SFX sintéticos (sin assets) para disparos, daño y aparición de bosses.
- **¿Por qué algunos símbolos no se veían?**
  Era un tema de fuente/render de glifos, no de vectores. Se mejoró el fallback de fuente simbólica y se normalizaron algunos iconos.


## Systems expansion

- New procedural 8-bit audio module: `game/systems/audio_system.py`
  - menu pulse loop
  - gameplay BPM pulse loop
  - final archetype stingers
  - SFX (shoot/dash/damage/boss spawn)
- New dynamic powers module: `game/systems/power_system.py`
  - active + passive powers integrated into level-up cards and player loop
- Omega final boss expanded to 3 phases in `game/entities/boss.py`
  - Reflection
  - Inversion
  - Dual Manifestation
- FINAL state now shows post-run archetype resolution with world distortion metrics.
