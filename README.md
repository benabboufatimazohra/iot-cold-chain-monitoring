# IoT Cold Chain Monitoring

IoT prototype that monitors the storage temperature of a medical analysis laboratory, where samples and reagents must stay between **2 °C and 8 °C**.

An **ESP8266 + DHT11** sensor sends temperature and humidity over Wi-Fi to a **Django REST Framework** API. The server stores every reading, opens an incident when the temperature leaves the safe range and closes it automatically when it comes back. A web dashboard shows the live values, escalates alerts to operators and keeps an incident archive for audits.

Academic team project, ENSA Oujda (GSEIR program), 2025–2026.

## Why

Manual temperature logs are discontinuous, error-prone and give no alert at night or on weekends. A fridge failure can mean lost stock, health risks and failed audits.

## Features

- **Data ingestion**: `POST /api/post/` receives `{"temp": …, "hum": …}` JSON from the ESP8266; the server timestamps each reading
- **Automatic incidents**: when T < 2 °C or T > 8 °C an incident is opened, its out-of-range counter and peak temperature are tracked, and it closes on the first in-range reading
- **Live dashboard**: polls `GET /latest/` every 5 s and shows temperature, humidity and the age of the last reading
- **Operator escalation (3 levels)** in the dashboard, based on the incident counter
- **Email alerts** via SMTP
- **History charts** for temperature and humidity (Chart.js)
- **Incident archive and detail pages** for traceability

## Architecture

```
ESP8266 + DHT11 ──Wi-Fi / HTTP POST (JSON)──▶ Django REST API ──▶ SQLite
                                                   │
                       Browser dashboard ◀──HTTP polling (5 s)──┘
                       (JavaScript, Chart.js)
```

| Part | Technology |
|---|---|
| Sensor node | ESP8266, DHT11 |
| Backend | Python, Django 5.2, Django REST Framework |
| Database | SQLite |
| Front end | Django templates, vanilla JavaScript, Chart.js |

## Main endpoints

| Method | URL | Purpose |
|---|---|---|
| POST | `/api/post/` | Store a new reading (used by the ESP8266) |
| GET | `/api/` | All readings |
| GET | `/latest/` | Latest reading (dashboard) |
| GET | `/incident/status/` | Current open incident |
| POST | `/incident/update/` | Operator acknowledgment + comment |
| GET | `/incident/archive/` | Incident archive page |

## Run locally

```bash
python -m venv venv
venv\Scripts\activate          # Windows  (Linux/macOS: source venv/bin/activate)
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

Email alerts need the environment variables listed in [`.env.example`](.env.example) (Gmail address, Gmail app password, recipients). Without them the app runs normally and simply sends no email.

## Next steps

- Authentication for operators
- Configurable thresholds per fridge
- CSV/PDF export of readings and incidents
- Push updates (WebSocket / MQTT) instead of polling

## Team

- Basma FOULLANE
- Fatima Zohra BENABBOU

The original repository is maintained by Basma Foullane. This copy was republished without its commit history to remove private credentials.
