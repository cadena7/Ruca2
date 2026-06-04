#!/usr/bin/env bash
set -euo pipefail

# --- Temperatura ---
get_temp() {
  if command -v vcgencmd >/dev/null 2>&1; then
    # Salida típica: temp=48.7'C
    local t
    t=$(vcgencmd measure_temp 2>/dev/null | sed -E "s/temp=([0-9.]+)'C/\1 °C/")
    [[ -n "$t" ]] && echo "$t" && return
  fi
  # Fallback leyendo del kernel
  if [[ -r /sys/class/thermal/thermal_zone0/temp ]]; then
    awk '{printf "%.1f °C\n", $1/1000}' /sys/class/thermal/thermal_zone0/temp
    return
  fi
  echo "N/D"
}

# --- Throttling (si existe vcgencmd) ---
get_throttled() {
  if command -v vcgencmd >/dev/null 2>&1; then
    local th
    th=$(vcgencmd get_throttled 2>/dev/null | awk -F= '{print $2}')
    if [[ "$th" == "0x0" || "$th" == "0x00000" ]]; then
      echo "OK (sin throttling)"
    else
      # Nota: mostramos el código hex. Si lo deseas, luego lo decodificamos por bits.
      echo "Atención (código: $th)"
    fi
  else
    echo "N/D"
  fi
}

# --- Memoria (free -n) ---
get_mem() {
  # Usamos -n (no forzar actualización) y formateamos legible
  # Campos: total used free shared buff/cache available
  if free -n >/dev/null 2>&1; then
    free -n -h | awk '
      /^Mem:/ {printf "%s usados / %s totales (%s disponibles)\n", $3, $2, $7}
    '
  else
    # Fallback sin -n
    free -h | awk '
      /^Mem:/ {printf "%s usados / %s totales (%s disponibles)\n", $3, $2, $7}
    '
  fi
}

# --- Disco (df -h) ---
get_disk() {
  # Mostramos raíz y /boot si existe
  local root boot
  root=$(df -h / 2>/dev/null | awk 'NR==2{printf "%s usados de %s (%s libres, %s ocupado) en %s\n",$3,$2,$4,$5,$6}')
  echo "$root"
  if mountpoint -q /boot 2>/dev/null; then
    boot=$(df -h /boot 2>/dev/null | awk 'NR==2{printf "%s usados de %s (%s libres, %s ocupado) en %s\n",$3,$2,$4,$5,$6}')
    echo "$boot"
  fi
}

# --- Salida ---
echo "📊 ESTADO DEL SISTEMA (Raspberry Pi)"
echo
echo "🌡️  Temperatura CPU : $(get_temp)"
echo "🚦 Throttling       : $(get_throttled)"
echo "🧠  Memoria RAM     : $(get_mem)"
echo "💾  Discos          :"
get_disk
echo
echo "✅ Listo."
