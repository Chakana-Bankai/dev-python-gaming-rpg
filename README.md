# Minimal Procedural Roguelike (Pygame)

Roguelike 2D **top-down** minimalista hecho en **un solo archivo Python** (`roguelike_pygame.py`) usando Pygame.

El juego incluye:
- Generación procedural de habitaciones conectadas en grilla
- Enemigos por habitación y puertas que se abren al limpiar la sala
- Movimiento WASD, dash, disparo al mouse
- Sistema de vida, invulnerabilidad temporal, knockback
- Progresión por experiencia y nivel
- Estados de juego: `MENU`, `PLAYING`, `GAME_OVER`

---

## Requisitos

- Python **3.10+** (recomendado 3.11 o 3.12)
- Dependencias en `requirements.txt`

---

## Instalación

### 1) Clonar repo

```bash
git clone <url-del-repo>
cd dev-python-gaming-rpg
```

### 2) Crear y activar entorno virtual

Linux/macOS:

```bash
python -m venv .venv
source .venv/bin/activate
```

Windows (PowerShell):

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3) Instalar dependencias

```bash
pip install -r requirements.txt
```

---

## Ejecutar el juego

```bash
python roguelike_pygame.py
```

---

## Controles

- `WASD`: mover personaje
- `Click izquierdo`: disparar hacia el mouse
- `Shift (izq/der)`: dash
- `Enter`: iniciar partida (desde menú)
- `R`: reiniciar (en Game Over)
- `ESC`: salir

---

## Estructura del proyecto

```text
.
├── roguelike_pygame.py  # Juego completo en un archivo
├── requirements.txt     # Dependencias para ejecución
└── README.md            # Guía de instalación y uso
```

---

## Solución de problemas

### No abre ventana en Linux (headless/servidor)
Si estás en un entorno sin interfaz gráfica, Pygame no podrá abrir la ventana del juego.
Ejecuta en una sesión con escritorio (X11/Wayland) o en tu máquina local.

### Error de instalación de pygame
Asegúrate de tener `pip` actualizado:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

---

## Notas técnicas

- El loop está limitado a **60 FPS** con `clock.tick(60)`.
- El movimiento usa **delta time** para ser estable entre equipos.
- No se usan assets externos: solo colores y rectángulos.
