# Live Sports · canales

Servicio que publica qué canal de España emite cada partido, para la app Live Sports.

Cada 3 horas, GitHub Actions descarga la guía de TV de [EPG_dobleM](https://github.com/davidmuma/EPG_dobleM), se queda con las emisiones deportivas (canal, hora, competición, equipos o jugadores y si es en directo) y publica `channels.json` en GitHub Pages.

## Probar en local

```bash
python3 build_channels.py public/channels.json
```

## Formato

```json
{
  "generated": "2026-11-02T21:30:00Z",
  "broadcasts": [
    {"ch": "M+ LaLiga", "start": "2026-11-02T19:50:00Z", "end": "2026-11-02T22:00:00Z", "live": true,
     "sport": "Fútbol", "comp": "LALIGA EA SPORTS", "home": "RC Deportivo", "away": "CA Osasuna", "detail": "Jornada 11"}
  ]
}
```

`home` y `away` solo aparecen cuando la guía nombra el partido; si no (p. ej. "TBC · Torneo de París"), la app lo usa a nivel de torneo.

La guía la recopila una comunidad a partir de los datos de los operadores. Para uso comercial conviene sustituirla por un proveedor de guía de TV con licencia: solo hay que cambiar `GUIDE_URL` y, si cambia el formato, `parse_title`.
