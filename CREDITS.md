# Credits / Créditos

## This project / Este proyecto

**Sebastian Rincon** ([@rinconsebastian](https://github.com/rinconsebastian))

- Flashed and tested real Sengled **W31-N13H** bulbs, a model that was not on the
  upstream list of tested bulbs.
  *Flasheó y probó bombillas **W31-N13H** reales, un modelo que no estaba en la
  lista de modelos probados del proyecto original.*
- Verified the GPIO/PWM pin mapping channel by channel and found that a commonly
  shared mapping (GPIO12/13/14) leaves the bulb without green.
  *Verificó canal por canal el mapeo de pines y encontró que un mapeo que circula
  (GPIO12/13/14) deja la bombilla sin verde.*
- Calibrated by eye the cold-white mix that makes Alexa's "cold white" and
  "warm white" actually look different.
  *Calibró a ojo la mezcla de blanco frío que hace que el "blanco frío" y el
  "blanco cálido" de Alexa se vean distintos.*
- Wrote the step-by-step guide, the troubleshooting notes and the helper tool.
  *Escribió la guía paso a paso, el troubleshooting y la herramienta de apoyo.*

## Original work this project builds on / Trabajo original en el que se basa

| Project | Author | What it provides | License |
|---|---|---|---|
| [SengledTools](https://github.com/HamzaETTH/SengledTools) | **HamzaETTH** | Local pairing (fake Sengled cloud, MQTT/TLS broker), OTA upload of the shim. The heart of the whole process. | No license published. **Not redistributed here**: `setup` downloads it from its official repository. |
| Sengled-Rescue (`firmware/shim.bin` inside SengledTools) | **Matt Falcon (FalconFour)** and contributors | The tiny on-bulb web flasher that backs up the chip and writes Tasmota. | MIT |
| [Tasmota](https://github.com/arendst/Tasmota) | **Theo Arends** and the Tasmota contributors | The open firmware running on the bulb afterwards. | GPL-3.0. Downloaded from its official releases. |
| [Tasmota templates](https://templates.blakadder.com/) | **blakadder** and contributors | Sengled template references. | — |
| [SengledTools issue #37](https://github.com/HamzaETTH/SengledTools/issues/37) | Community | Reported the W31-N13H WLED pin order (12, 15, 13, 4) that pointed to the right mapping. | — |

Thank you all. Without your work these bulbs would be e-waste.
*Gracias a todos. Sin su trabajo estas bombillas serían basura electrónica.*

"Sengled" is a trademark of its owner. This project is not affiliated with,
endorsed by or supported by Sengled.
*"Sengled" es una marca de su propietario. Este proyecto no está afiliado ni
respaldado por Sengled.*
