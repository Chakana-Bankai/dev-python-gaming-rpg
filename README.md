# Roguelike 2D Iniciático Evolutivo

Experiencia roguelike modular con progresión simbólica persistente, narrativa iniciática por escenas y dificultad adaptativa.

## Ejecutar

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m game.main
```

## Arquitectura (Plan C)

```text
game/
├── main.py
├── engine/
│   ├── scene_manager.py
│   ├── state_manager.py
│   └── save_system.py
├── scenes/
│   ├── intro_scene.py
│   ├── narrative_scene.py
│   ├── gameplay_scene.py
│   ├── boss_scene.py
│   ├── transition_scene.py
│   └── ending_scene.py
├── systems/
│   ├── difficulty_system.py
│   ├── progression_system.py
│   ├── procedural_system.py
│   ├── particle_system.py
│   ├── camera_system.py
│   ├── geometry_system.py
│   └── audio_system.py
└── data/
    ├── narrative.json
    ├── progression.json
    ├── config.json
    └── world_memory.json
```

## Qué aporta esta actualización

- **Narrativa modular**: 6 fragmentos iniciáticos con variaciones y texto desbloqueable por lucidez.
- **Persistencia real**: runs completados, muertes, tiempos de sala, conciencia, seed y arquetipos desbloqueados.
- **Dificultad reactiva**: ajusta velocidad/densidad según precisión, daño recibido y tiempo por sala.
- **Visual minimalista mejorado**: partículas ligeras, cámara dinámica (shake/nudge/zoom boss) y paletas simbólicas.
- **Bucle evolutivo**: cada ciclo aumenta lucidez y transforma la experiencia sin romper rendimiento.

- **Presentación visual reforzada**: resolución base FHD (1920x1080), textos más grandes y pantalla final negra con resumen persistente.

## Notas

El `GameManager` original se mantiene como núcleo de combate para preservar compatibilidad, ahora orquestado por el sistema de escenas.
