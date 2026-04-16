# AirQualityCheck

## Infrastructure

```
Mikrocontroller
- 1 Temp Sensor
- 1 Aktor (Fenster auf zu / Steppermotor)
- 1 RGB LED (Status)
- 1 Speaker

Datenaustauch mit MQTT

Docker.env
- Speicher der Daten in postgresDB
- Steuert Motor
- gettet von Wetter API Daten von outside
- sound wenn sachen machen
- Frontend mit Webinterface mit Datenanzeige
```

Motor Commands

start
stop
steps:N
rotate:N

home/sensor/motor/command
rotate:360
rotate:-360

