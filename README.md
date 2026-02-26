# Symbolic Roguelike (Pygame, Clean Architecture)

Proyecto roguelike top-down modular en **múltiples archivos** con arquitectura limpia para Pygame.

## Estructura

```text
game/
├── main.py
├── settings.py
├── game_manager.py
├── entities/
│   ├── player.py
│   ├── enemy.py
│   ├── boss.py
│   ├── super_boss.py
│   └── bullet.py
├── systems/
│   ├── level_system.py
│   ├── door_system.py
│   ├── upgrade_system.py
│   ├── item_system.py
│   ├── combat_system.py
│   └── narrative_system.py
├── ui/
│   ├── hud.py
│   ├── level_up_screen.py
│   └── end_screen.py
└── utils/
    ├── timers.py
    └── helpers.py
```

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Ejecución

```bash
python -m game.main
```

## Controles

- WASD: mover
- Click izquierdo: disparar
- Shift: dash
- Enter: iniciar
- 1/2/3: elegir mejora al subir nivel
- R: reiniciar en final/game over
- ESC: salir
