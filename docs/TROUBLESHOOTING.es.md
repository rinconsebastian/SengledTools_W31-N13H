# Solución de problemas

[English](TROUBLESHOOTING.md) · [Volver al README](../README.es.md)

Todo lo de esta guía pasó en pruebas reales con bombillas W31-N13H. Busca el paso donde te
quedaste. Si tienes dudas con una bombilla ya flasheada, empieza por:

```bash
python w31n13h.py check --ip <ip-bombilla>
```

Te dice si la bombilla responde y, si no, la causa más probable.

---

## Preparación (`w31n13h.py setup`)

**pip falla compilando `pyyaml`: "Unable to find a compatible Visual Studio installation"**
Las versiones muy nuevas de Python no tienen paquete listo de PyYAML, así que pip intenta
compilarlo. `setup` ya lo evita con `PYYAML_FORCE_LIBYAML=0`, que lo instala en modo Python
puro. Si instalas SengledTools a mano, define esa variable antes.

**"Python 3.10 or newer is required"**
Instala un Python reciente desde [python.org](https://www.python.org/downloads/). En
Windows, prueba `py w31n13h.py ...` si `python` apunta a una versión vieja.

**Checksum mismatch (no coinciden las sumas)**
La descarga se dañó o cambió. Ejecuta `python w31n13h.py setup --force`. Si sigue fallando
con las versiones probadas, no continúes; abre un issue.

---

## Emparejamiento (`sengled --setup-wifi`)

**No aparece la red `Sengled_Wi-Fi Bulb_XXXXXX`**
Resetea otra vez: apaga y prende la bombilla 5 o más veces seguidas hasta que parpadee.
Mira la [animación del reset](https://github.com/HamzaETTH/SengledTools/blob/master/docs/RESET_PROCEDURES.md).

**"Waiting for bulb response…" sin fin**
En ese momento el PC debe estar conectado a la red Wi-Fi de la bombilla. Desconéctate y
vuelve a conectarte; la herramienta sigue reintentando.

**Mi red no aparece en la lista, o la bombilla nunca se conecta**
La bombilla solo usa **2.4 GHz**. Si tu router solo emite en 5 GHz, activa la banda de
2.4 GHz o crea una red aparte de 2.4 GHz. Las redes en malla con el mismo nombre en ambas
bandas funcionan.

**La verificación agota el tiempo ("make sure no firewall is blocking")**
La bombilla entró a tu Wi-Fi pero no llega a tu PC.
- El PC debe haber vuelto a la **misma** red de casa.
- Cuando Windows pregunte, permite Python en redes **privadas**.
- Desactiva el "aislamiento de AP" o "aislamiento de clientes" del router.
- Prueba: desde un celular en el mismo Wi-Fi abre `http://<ip-del-pc>:57542/jbalancer/new/bimqtt`. Si no muestra texto, arregla primero la red.

**Terminó el emparejamiento pero nunca ofreció flashear**
Así funciona `--setup-wifi`. Sigue con el paso 3 del README (`--run-servers` +
`--upgrade`).

---

## Subida del shim (`--run-servers` + `--upgrade`)

**"HTTP server failed on port 57542. Port is already in use"**
Otra copia de SengledTools sigue abierta. Normalmente es el emparejamiento esperando en
*"Press Enter to quit"*. Ciérrala y vuelve a iniciar `--run-servers`.

**`--upgrade` dice "Port 8883 is not listening"**
Primero inicia `python w31n13h.py sengled --run-servers` en otra terminal y déjala abierta.

**La bombilla nunca aparece en `--run-servers`**
- Espera hasta un minuto.
- Apaga y prende la bombilla **una sola vez**.
- Verifica que el PC tenga la **misma IP** que durante el emparejamiento, porque a la bombilla se le dio esa dirección. Reserva la IP del PC en el router, o vuelve a emparejar.

**La prueba `--brightness 30` no hace nada**
MQTT no está funcionando, así que no envíes `--upgrade`. Revisa el punto anterior.

**La bombilla reporta otro modelo distinto de W31-N13H, o `identifyNO` no es ESP8266**
Detente. Solo las bombillas ESP8266 (WF863) se pueden flashear así. Otras, como
WF864/MX1290 o EMW3091, quedarían inservibles. Aún se pueden controlar localmente con
SengledTools.

---

## Sengled-Rescue (http://192.168.4.1)

**No aparece la red `Sengled-Rescue`**
Revisa que la terminal A haya mostrado `Served firmware: shim.bin (495728 bytes)` y espera
3–5 minutos. No sigas apagando y prendiendo la bombilla.

**La página es lentísima o carga a medias**
Es normal; la bombilla es un dispositivo muy pequeño. Refresca hasta que cargue completa.

**"write blocked (overlaps running slot)" y el botón Flash está gris**
Pulsa **Relocate to ota_1**. Espera a que la bombilla reinicie, reconéctate a
`Sengled-Rescue` y vuelve a flashear.

**¿Qué archivo flasheo?**
`work/tasmota.bin`, eligiendo **boot**. Nunca el archivo `.bin.gz`.

---

## Después de flashear Tasmota

**Qué significa la luz azul**
Sin plantilla, Tasmota todavía no controla los colores, así que la luz solo muestra su
estado:

| Luz | Significa | Siguiente paso |
|---|---|---|
| Azul parpadeando | Tasmota funciona y no tiene Wi-Fi configurado. | Conéctate a `tasmota_XXXXXX-####` y configura tu Wi-Fi. |
| Azul fijo | Se conectó a tu Wi-Fi. | Busca su IP en el router. |

**Azul fijo y el router la muestra conectada, pero sin IP válida (no responde ni al ping)**
Nos pasó aunque los datos del Wi-Fi eran correctos. Apaga y prende la bombilla **una sola
vez**. Tras ese reinicio obtuvo su IP y todo siguió con normalidad. Luego abre
`http://<ip>` en el navegador. Reservar su IP en el router (reserva DHCP) ayuda para la
próxima vez. No hagas varios ciclos rápidos: activan los modos de recuperación que se
explican más abajo.

**La página web carga, pero los comandos fallan con respuesta vacía (`curl: (52)`)**
La **HTTP API de Tasmota está desactivada**, que es lo predeterminado en Tasmota 16. Ve a
**Configuration → Configure Other → HTTP API → Save**. `check` detecta este caso.

**Se pierden pings o la primera petición agota el tiempo**
El ahorro de energía de Tasmota (sleep dinámico) hace que la bombilla a veces responda
lento. Es normal; solo reintenta. La herramienta reintenta sola.

---

## Colores y Alexa

**El "blanco frío" y el "blanco cálido" de Alexa se ven iguales**
Faltan `SetOption106 1` y `VirtualCT`. Ejecuta `configure`. El README explica por qué.

**El blanco frío volvió a ser azulado después de un corte de luz**
Tasmota **no** guarda `VirtualCT` en la memoria. La regla de arranque `Rule3` lo vuelve a
aplicar. `check` muestra `Rule3: MISSING` cuando esa regla falta; ejecuta `configure` (o
`calibrate` → `s`).

**El blanco frío tiene un tinte**
Ejecuta `python w31n13h.py calibrate --ip <ip>` y corrígelo paso a paso:

| Lo ves | Tecla | Cambio |
|---|---|---|
| algo rosado | `p` | más verde |
| algo verdoso | `g` | menos verde |
| muy azul | `b` | menos azul |
| muy amarillo / cálido | `y` | más azul |
| muy tenue | `+` | más LED blanco y un poco de azul |

Las cámaras de los celulares corrigen el balance de blancos, así que confía en tus ojos y
no en el código hexadecimal que muestre la cámara.

**El blanco frío es más tenue que el cálido**
Es lo esperado. El cálido tiene su propio LED, más eficiente, mientras que el frío sale
sobre todo de los LED de color. `+` en `calibrate` sube la parte del LED blanco, pero si te
pasas el blanco "frío" queda más neutro.

**Colores equivocados, o sin verde**
La plantilla es incorrecta. Usa la verificada del README. El mapeo GPIO12/13/14 que
circula no tiene canal verde.

**La bombilla perdió de repente su configuración: aparece "Generic" y los colores no responden**
Es la **protección contra bucles de arranque** de Tasmota (`SetOption36`). Cuando la
bombilla se reinicia por un error (excepción o watchdog) varias veces seguidas, cada vez a
menos de 10 segundos de arrancar, Tasmota va restableciendo ajustes por pasos. En el 4.º
paso **borra los pines de la plantilla**. Le pasó a una de nuestras bombillas; no sabemos
qué causó sus reinicios.
- **Solución:** ejecuta `configure` otra vez. El nombre y el Wi-Fi se conservan.
- **Si se repite:** `SetOption36 0` desactiva esta protección. A cambio, Tasmota ya no podrá recuperarse solo de un bucle de fallos real. Abre también un issue, porque la causa sigue sin conocerse.

**Apagué y prendí la bombilla muchas veces y volvió a la red `tasmota_`**
Tasmota borra **todos** los ajustes, incluido el Wi-Fi, tras **7 ciclos rápidos de
apagado y encendido**. Es la
[recuperación por ciclos rápidos](https://tasmota.github.io/docs/Device-Recovery/).
Configura de nuevo el Wi-Fi, activa la HTTP API y ejecuta `configure`. Si tu
electricidad es inestable, `SetOption65 1` desactiva esta función (pero también pierdes
esta vía de recuperación).

**Alexa no encuentra la bombilla**
- Comprueba que `Emulation` sea `2` (con `check`, o en la consola `Emulation`).
- El Echo y la bombilla deben estar en la misma red o VLAN.
- En la app de Alexa agrégala como **Luz → Philips Hue** y dale unos minutos al descubrimiento.

**Cambié el nombre pero Alexa sigue mostrando el anterior**
Renómbrala en la app de Alexa, o bórrala ahí y vuelve a buscar dispositivos.

**La descripción Hue dice "Amazon-Echo-HA-Bridge"**
Así se identifica la emulación Hue de Tasmota. Alexa muestra el `FriendlyName1` de la
bombilla.

---

## Volver atrás

| Situación | Qué hacer |
|---|---|
| Un ajuste dañó el comportamiento de la bombilla | Restaura un `.dmp` en **Configuration → Restore Configuration**, o ejecuta `configure` otra vez. |
| Tasmota no arranca | Abre la bombilla, conecta un adaptador serie y escribe tu respaldo completo con `esptool.py`. Ver las [notas de Sengled-Rescue](https://github.com/HamzaETTH/SengledTools/tree/master/firmware/sengled_ota). |

¿Sigues atascado? Abre un issue con la salida de `python w31n13h.py check --ip <ip>`.
Si en lo que pegues aparece la clave de tu Wi-Fi, bórrala antes.
