# SengledTools W31-N13H — Tasmota para bombillas Sengled W31-N13H, 100% local

[English](README.md) · [Solución de problemas](docs/TROUBLESHOOTING.es.md) · [Créditos](CREDITS.md) · [Licencia MIT](LICENSE)

La nube de Sengled ya no existe, así que sus bombillas Wi-Fi dejaron de funcionar con la
app y con Alexa. Esta guía revive una **Sengled W31-N13H** (color + blanco, A19) con el
firmware libre [Tasmota](https://tasmota.github.io/), **sin abrir la bombilla, sin soldar
y sin ninguna nube**.

Es un complemento del excelente [HamzaETTH/SengledTools](https://github.com/HamzaETTH/SengledTools),
que hace la parte difícil (el emparejamiento y la subida por OTA). Este repositorio añade
lo que la W31-N13H necesitaba y faltaba:

- ✅ **Una plantilla de Tasmota verificada.** Cada canal de color se probó en bombillas reales.
- ✅ **Blanco cálido *y* frío de verdad en Alexa.** La bombilla tiene un solo LED blanco, el cálido. El frío se mezcla con los LED de color, y la mezcla se calibró a ojo.
- ✅ **Una herramienta pequeña, `w31n13h.py`.** Cubre la preparación, la configuración, la calibración y los respaldos. Solo usa la librería estándar de Python.
- ✅ **Una guía de solución de problemas** hecha con cada problema que encontramos.

No necesitas cuenta, app ni IA: solo un PC con Wi-Fi, Python y un navegador.

> [!CAUTION]
> Flashear reemplaza el firmware original y **no se puede deshacer por Wi-Fi**.
> Si algo sale mal, la bombilla solo se recupera abriéndola y usando un adaptador serie.
> Haz el respaldo completo del paso 5. Lo haces bajo tu propio riesgo.

---

## Contenido

1. [Qué necesitas](#qué-necesitas)
2. [Cómo funciona](#cómo-funciona)
3. [Paso a paso](#paso-a-paso)
4. [Parámetros de color (lo importante)](#parámetros-de-color)
5. [Configurar sin la herramienta](#configurar-sin-la-herramienta)
6. [Respaldos y cómo volver atrás](#respaldos-y-cómo-volver-atrás)
7. [Referencia de la herramienta](#referencia-de-la-herramienta)
8. [Qué se probó](#qué-se-probó)
9. [Créditos y licencia](#créditos-y-licencia)

---

## Qué necesitas

| | |
|---|---|
| **Bombilla** | Sengled **W31-N13H**. El modelo está impreso en la bombilla. Durante el emparejamiento la herramienta debe mostrar `typeCode: W31-N13H` e `identifyNO: ESP8266`. |
| **PC** | Windows, Linux o macOS, con Wi-Fi. |
| **Python** | 3.10 o superior ([python.org](https://www.python.org/downloads/)). |
| **Red Wi-Fi** | Debe tener **2.4 GHz**, porque la bombilla no ve redes que solo son de 5 GHz. Las redes en malla (mesh) funcionan. |
| **Tiempo** | Unos 20–30 minutos para la primera bombilla y 10 para cada una adicional. |

> [!WARNING]
> Solo se pueden flashear así las bombillas con chip **ESP8266** (módulo Sengled WF863).
> Si el emparejamiento muestra otra cosa distinta de `ESP8266`, detente. Aún podrás
> controlarla localmente con SengledTools, pero no flashearla.

## Cómo funciona

```
 Tu PC                              La bombilla
 ─────                              ───────────
 1. Emparejar    ── Wi-Fi + dirección "nube" ──▶  firmware Sengled original
    (SengledTools se hace pasar por la nube y el broker MQTT de Sengled)
 2. Subida OTA   ── shim.bin por HTTP ─────────▶  Sengled-Rescue (mini flasheador)
 3. Navegador    ── respaldo + tasmota.bin ────▶  Tasmota
 4. w31n13h.py   ── plantilla + colores ───────▶  Tasmota, lista para Alexa
```

1. **Emparejar.** SengledTools le da a la bombilla la clave de tu Wi-Fi y le dice que tu PC es "la nube".
2. **Subida OTA.** Con el propio mecanismo de actualización de Sengled, la bombilla descarga un programa pequeño llamado **Sengled-Rescue**.
3. **Navegador.** Sengled-Rescue crea su propia red Wi-Fi con una página web. Ahí respaldas el chip y subes Tasmota.
4. **`w31n13h.py`.** Tasmota se conecta a tu Wi-Fi, y `w31n13h.py` aplica los pines, la emulación Hue y la calibración de color.

## Paso a paso

Abre una terminal en esta carpeta. En Windows, si `python` no funciona, usa `py`.

### 1. Preparar el PC (una sola vez)

```bash
python w31n13h.py setup
```

Descarga SengledTools (en la versión exacta que se probó) y el firmware de Tasmota en
`work/`, verifica sus sumas SHA-256 y crea un entorno de Python aislado. No instala nada
en el sistema.

### 2. Emparejar la bombilla

1. **Resetea la bombilla de fábrica.** Apágala y préndela **5 o más veces seguidas** hasta que parpadee. Aparece una red Wi-Fi llamada `Sengled_Wi-Fi Bulb_XXXXXX`. ([animación del reset](https://github.com/HamzaETTH/SengledTools/blob/master/docs/RESET_PROCEDURES.md))
2. **Inicia el emparejamiento:**
   ```bash
   python w31n13h.py sengled --setup-wifi
   ```
3. **Sigue las instrucciones.** Cuando lo pida, conecta el PC a la red de la bombilla. Elige tu red de **2.4 GHz** en la lista y escribe su clave. El PC vuelve a tu red de casa y la bombilla lo contacta.
4. **Comprueba el resultado:**
   - Debe mostrar `typeCode: W31-N13H`, `identifyNO: ESP8266` y *UDP control test passed*.
   - **Anota la dirección MAC de la bombilla.**
5. **Cierra la herramienta:** pulsa Enter para salir.

> `--setup-wifi` **no** ofrece flashear. Es normal; eso es el paso siguiente.

### 3. Subir el shim Sengled-Rescue

Necesitas **dos terminales**.

**Terminal A** – inicia los servidores locales y déjalos corriendo:

```bash
python w31n13h.py sengled --run-servers
```

Espera a que aparezca `Served GET on /jbalancer/new/bimqtt`, que significa que la bombilla se reconectó. Puede tardar hasta un minuto.

**Terminal B** – prueba opcional: la bombilla debe bajar su brillo.

```bash
python w31n13h.py sengled --mac AA:BB:CC:DD:EE:FF --brightness 30
```

Luego envía el shim. Usa tu MAC; la ruta va exactamente así:

```bash
python w31n13h.py sengled --mac AA:BB:CC:DD:EE:FF --upgrade firmware/shim.bin
```

Confirma las dos advertencias. En la **terminal A** verás
`Served firmware: shim.bin (495728 bytes)`. Desde ese momento ya no hay vuelta al
firmware de Sengled. Detén la terminal A con Ctrl+C.

### 4. Esperar a Sengled-Rescue

En 1–3 minutos aparece una red Wi-Fi llamada **`Sengled-Rescue`**. Conecta el PC a ella y
abre **http://192.168.4.1**. La página es muy lenta; refresca hasta que cargue.

### 5. Respaldar y flashear Tasmota

1. **Respalda el chip completo.** Elige **full** y pulsa **Backup selected**. Guarda el archivo de 2 MB en un lugar seguro, con un nombre que identifique la bombilla. **Es tu única forma de volver atrás.**
2. **Sube Tasmota.** Elige **boot**, selecciona `work/tasmota.bin` (*no* un archivo `.gz`) y pulsa **Flash selected**.
3. **Si dice "write blocked (overlaps running slot)":** pulsa **Relocate to ota_1**, reconéctate a `Sengled-Rescue` y repite el punto 2.

La bombilla reinicia con Tasmota y empieza a **parpadear en azul**. Eso significa que
Tasmota está funcionando y espera que configures el Wi-Fi.

### 6. Conectar Tasmota a tu Wi-Fi

1. Conéctate a la red `tasmota_XXXXXX-####` y abre **http://192.168.4.1**.
2. Pon tu Wi-Fi de 2.4 GHz y guarda. Cuando la bombilla se conecta a tu red, la luz pasa a **azul fijo**.
3. Busca la IP nueva de la bombilla en la lista de clientes del router (el nombre empieza por `tasmota-`).

> [!IMPORTANT]
> **¿Azul fijo pero sin IP válida?** En nuestra prueba los datos del Wi-Fi eran correctos,
> pero el router mostraba la bombilla conectada sin una IP válida, y no respondía. Apaga y
> prende la bombilla **una sola vez**. Tras ese reinicio obtuvo su IP y todo siguió con
> normalidad. Solo un ciclo: varios seguidos y rápidos activan los modos de recuperación de
> Tasmota (ver [Solución de problemas](docs/TROUBLESHOOTING.es.md)).

Consejo: reserva esa IP para la MAC de la bombilla en tu router (reserva DHCP).

### 7. Activar la HTTP API de Tasmota

Tasmota 16 viene con la HTTP API **desactivada**. Abre `http://<ip-bombilla>` →
**Configuration → Configure Other** → marca **HTTP API** → **Save**.

### 8. Aplicar la configuración W31-N13H

```bash
python w31n13h.py configure --ip 192.168.1.50 --name "Sengled cocina"
```

La herramienta tarda alrededor de un minuto, y la bombilla se reinicia dos veces mientras tanto. Hace lo siguiente:

- aplica la plantilla;
- pone el nombre;
- activa la emulación Hue;
- configura la mezcla de blanco cálido/frío, con una regla de arranque para que no se pierda;
- verifica cada ajuste;
- guarda un respaldo de la configuración en `backups/`;
- deja la bombilla en **blanco frío** para que la revises.

### 9. Afinar el blanco frío (solo si hace falta)

Los LED varían un poco entre bombillas. Si el blanco frío se ve algo rosado, verdoso,
azulado o amarillento:

```bash
python w31n13h.py calibrate --ip 192.168.1.50
```

Responde con una tecla (`p` rosado, `g` verdoso, `b` azulado, `y` amarillento, `+` más
brillo…) hasta que se vea neutro, y luego `s` para guardar.

### 10. Agregarla a Alexa

En la app de Alexa ve a **Agregar dispositivo → Luz → Philips Hue**, o di
*"Alexa, descubre dispositivos"*. La bombilla aparece con el nombre que le diste.

## Parámetros de color

Este es el conocimiento que aporta este repositorio. Los valores también están en
[`config/w31-n13h.json`](config/w31-n13h.json).

### Plantilla (pines)

```json
{"NAME":"Sengled W31-N13H","GPIO":[0,0,0,0,419,0,0,0,416,418,0,417,0,0],"FLAG":0,"BASE":18}
```

| GPIO | Tasmota | LED |
|---|---|---|
| GPIO12 | PWM1 | rojo |
| GPIO15 | PWM2 | verde |
| GPIO13 | PWM3 | azul |
| GPIO4 | PWM4 | blanco **cálido** (el único LED blanco) |

> [!NOTE]
> Un mapeo que circula en internet (GPIO12 → PWM1, GPIO13 → PWM3, GPIO14 → PWM4) es
> **incorrecto** para esta bombilla: no tiene canal verde. La tabla de arriba se verificó
> canal por canal.

### Por qué el blanco necesita trabajo extra

La W31-N13H no tiene LED de blanco frío. Por defecto Tasmota manda todos los blancos al
LED cálido, así que en Alexa **"blanco frío" y "blanco cálido" se ven iguales**. El
firmware original de Sengled fabricaba el blanco frío mezclando los LED de color, y
Tasmota puede hacer lo mismo:

| Comando | Qué hace |
|---|---|
| `SetOption106 1` | Activa una *temperatura de color virtual* para bombillas RGBW. |
| `VirtualCT {"153":"F8E2B480","500":"000000FF"}` | Lo más frío (153 mireds ≈ 6500 K) = R F8, G E2, B B4 + LED blanco al 50%. Lo más cálido (500 mireds ≈ 2000 K) = solo el LED blanco. Los tonos intermedios se mezclan. |
| `Rule3 ON System#Boot DO VirtualCT {...} ENDON` + `Rule3 1` | **Obligatorio.** Tasmota no guarda `VirtualCT` en la memoria, así que sin esta regla el blanco frío vuelve a ser azulado tras cada corte de luz. |
| `SetOption30 1` + `Emulation 2` | Emulación Hue, para que Alexa controle la bombilla de forma directa y local. |

**Valores de blanco frío probados** (`RRGGBBWW`):

| Valor | Resultado |
|---|---|
| `FFFFFF00` | El de fábrica de Tasmota: demasiado azul. |
| `F8D89640` | Neutro pero bastante más tenue que el blanco cálido. |
| **`F8E2B480`** | **Por defecto.** Neutro y más brillante (LED blanco al 50%). |
| `F8EAB480` | El mismo con un poco más de verde, para una bombilla que se veía algo rosada. |

Aun así, el blanco frío siempre será algo más tenue que el cálido. El cálido usa un LED
dedicado y eficiente; el frío sale sobre todo de los LED de color, que son menos
eficientes. Los tonos medios ("blanco suave", "blanco") quedan en medio.

## Configurar sin la herramienta

Pega estas líneas en la **Consola** web de la bombilla (Tasmota → Tools → Console), una
por una. La bombilla se reinicia después de las dos primeras:

```
Backlog Template {"NAME":"Sengled W31-N13H","GPIO":[0,0,0,0,419,0,0,0,416,418,0,417,0,0],"FLAG":0,"BASE":18}; Module 0
Backlog FriendlyName1 Sengled cocina; DeviceName Sengled cocina; SetOption30 1; SetOption106 1; Emulation 2
VirtualCT {"153":"F8E2B480","500":"000000FF"}
Rule3 ON System#Boot DO VirtualCT {"153":"F8E2B480","500":"000000FF"} ENDON
Rule3 1
```

## Respaldos y cómo volver atrás

| Tienes | Cómo restaurar |
|---|---|
| Configuración de Tasmota (`.dmp`, de `configure`, `calibrate` o `backup`) | Web de la bombilla → **Configuration → Restore Configuration**. |
| Respaldo completo del chip (`.bin` de 2 MB, de Sengled-Rescue) | Solo con adaptador serie y `esptool.py`, abriendo la bombilla. Ver las [notas de Sengled-Rescue](https://github.com/HamzaETTH/SengledTools/tree/master/firmware/sengled_ota). |

Guarda tus respaldos fuera de este repositorio: `backups/`, `*.dmp` y `*.bin` están ignorados en git a propósito.

## Referencia de la herramienta

| Comando | Qué hace |
|---|---|
| `python w31n13h.py setup [--force] [--tasmota latest] [--upstream latest]` | Descarga SengledTools y Tasmota (por defecto, las versiones probadas), verifica sus sumas de control y crea el venv. |
| `python w31n13h.py sengled <opciones>` | Ejecuta SengledTools. Sus certificados y ajustes se quedan en `work/home`, no en tu perfil de usuario. |
| `python w31n13h.py check --ip IP` | Dice si la bombilla responde y por qué no (HTTP API apagada, IP equivocada…), y muestra la plantilla, los colores, la regla de arranque y la señal Wi-Fi. |
| `python w31n13h.py configure --ip IP --name NOMBRE [--cold RRGGBBWW] [--dry-run]` | Aplica la configuración W31-N13H completa. `--dry-run` solo muestra los comandos. |
| `python w31n13h.py calibrate --ip IP` | Ajuste interactivo del blanco frío; guarda el valor con su regla de arranque. |
| `python w31n13h.py backup --ip IP [--name NOMBRE]` | Descarga la configuración de Tasmota a `backups/`. |

Todos los comandos de bombilla aceptan `--password` si pusiste contraseña web en Tasmota.

## Qué se probó

| | |
|---|---|
| Bombillas | 2 × Sengled W31-N13H (WF863 / ESP8266EX, flash de 2 MB) |
| SengledTools | commit `7d5eadb` (2026-06-04) |
| Tasmota | 16.0.0 (`tasmota.bin`) |
| PC | Windows 11, Python 3.15 |
| Asistente | Alexa, con la emulación Hue de Tasmota |

Linux y macOS deberían funcionar, porque todo es Python puro, pero no se probaron.
Si los pruebas, abre un issue con tu resultado.

## Créditos y licencia

Pruebas, verificación de pines, calibración de color y documentación:
**Sebastian Rincon** ([@rinconsebastian](https://github.com/rinconsebastian)).

Basado en el trabajo de **HamzaETTH** ([SengledTools](https://github.com/HamzaETTH/SengledTools)),
**Matt Falcon / FalconFour** (shim Sengled-Rescue) y **Theo Arends y los colaboradores de
Tasmota**. Detalles completos en [CREDITS.md](CREDITS.md).

Los archivos de este repositorio están bajo la [licencia MIT](LICENSE): úsalos, cámbialos y
compártelos libremente, conservando el aviso de copyright. El software de terceros se
descarga desde sus fuentes oficiales y conserva su propia licencia; SengledTools no publica
licencia, así que **no** se redistribuye aquí.

Sin relación ni respaldo de Sengled.
