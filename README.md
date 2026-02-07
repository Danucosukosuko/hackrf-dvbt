# HackRF DVB-T (Windows / Python)

Este repositorio contiene una base para un decodificador DVB-T usando HackRF en
Windows con una interfaz gráfica para buscar canales y reproducirlos.

## Requisitos

- HackRF + drivers oficiales ("hackrf_info" en el PATH).
- Python 3.10+.
- Python VLC (`python-vlc`) y VLC Media Player para ver el vídeo embebido.
- Un demodulador DVB-T compatible (GNU Radio + gr-dtv, leandvb, etc.).

## Uso rápido

```bash
python main.py
```

1. Edita `demod_config.json` con el comando del demodulador (ver ejemplos abajo).
2. Define la frecuencia inicial y final (en MHz).
3. Pulsa **Buscar** para escanear cada 8 MHz.
4. Selecciona un canal y pulsa **Ver canal**.

## Ejemplos de demodulador

El programa ejecuta el comando indicado en `demod_config.json` y espera un flujo
MPEG-TS en UDP. Ajusta el comando según tu instalación.

### Opción 1: GNU Radio + gr-dtv + gr-osmosdr

Lanza un flowgraph que demodule DVB-T y envíe MPEG-TS a UDP. Puedes exportar tu
propio `.grc` a Python y llamarlo desde el comando.

### Opción 2: leandvb

`leandvb` puede recibir muestras I/Q desde `hackrf_transfer` y producir MPEG-TS
por UDP. Ejemplo (ajusta rutas y ganancias):

```bash
hackrf_transfer -f {freq_hz} -s {sample_rate_hz} -a 1 -g 40 -r - \
  | leandvb --ifile - --sr {sample_rate_hz} --freq {freq_hz} --bw {bandwidth_hz} \
  --udp {udp_host}:{udp_port}
```

El comando anterior debe copiarse a `demod_config.json` reemplazando los
placeholders disponibles.

## Placeholders disponibles en `demod_config.json`

- `{freq_hz}`
- `{bandwidth_hz}`
- `{sample_rate_hz}`
- `{udp_host}`
- `{udp_port}`
