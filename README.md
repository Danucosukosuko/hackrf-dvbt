# HackRF DVB-T (Windows / Python)

Este repositorio contiene una base para un decodificador DVB-T usando HackRF en
Windows con una interfaz gráfica para buscar canales y reproducirlos.

## Requisitos

- HackRF + drivers oficiales ("hackrf_info" en el PATH).
- Python 3.10+.
- Python VLC (`python-vlc`) y VLC Media Player para ver el vídeo embebido.
- Un demodulador DVB-T compatible que entregue MPEG-TS por UDP.

## Uso rápido

```bash
python main.py
```

1. Edita `demod_config.json` con el comando del demodulador (ver ejemplos abajo).
2. Define la frecuencia inicial y final (en MHz).
3. Pulsa **Buscar** para escanear cada 8 MHz.
4. Selecciona un canal y pulsa **Ver canal**.

## ¿Qué librerías/soluciones usar (sin GNU Radio ni leandvb)?

No existe un decodificador DVB‑T completo en Python puro. Para HackRF necesitas
un demodulador externo que entregue MPEG‑TS. Algunas alternativas posibles:

- **SDRangel** (con demodulador DVB‑T y salida UDP).
- **SDR++** (si cuenta con plugin DVB‑T en tu instalación).
- **Soluciones propietarias** que expongan MPEG‑TS por UDP.

Además, para hardware DVB‑T clásico (no HackRF), puedes usar **libdvbv5**
o herramientas de `dvb-apps` para generar el TS, pero esto no aplica a SDR.

## Ejemplos de demodulador

El programa ejecuta el comando indicado en `demod_config.json` y espera un flujo
MPEG-TS en UDP. Ajusta el comando según tu instalación.

### Opción 1: comando externo (demodulador con salida UDP)

```bash
<tu_demodulador> --freq {freq_hz} --bw {bandwidth_hz} --udp {udp_host}:{udp_port}
```

El comando anterior debe copiarse a `demod_config.json` reemplazando los
placeholders disponibles.

### Modo externo

Si tu demodulador se controla por su propia UI (por ejemplo SDRangel), puedes
usar `"mode": "external"` en `demod_config.json`. En ese modo la app **solo**
escucha el MPEG‑TS por UDP y necesitas retunar manualmente desde tu demodulador.

## Placeholders disponibles en `demod_config.json`

- `{freq_hz}`
- `{bandwidth_hz}`
- `{sample_rate_hz}`
- `{udp_host}`
- `{udp_port}`
