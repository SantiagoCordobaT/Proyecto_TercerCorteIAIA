# Guion de la presentación · CryptoRisk & Trend SBC

Diapositivas: `CryptoRisk_SBC.pptx` (12, cada una con notas del orador que sirven de guion). Duración sugerida: ~12 minutos.

| # | Diapositiva | Contenido clave | Apoyo visual |
| :-: | :--- | :--- | :--- |
| 1 | Portada | Título, integrantes, curso (IAIA), aviso académico | Logo / imagen de gráfico de velas |
| 2 | Problema y dominio | Swing trading en criptomonedas: decidir comprar o mantener liquidez con datos incompletos | Gráfico de precio con EMA200 y RSI |
| 3 | ¿Por qué un SBC? | Jerarquía datos → estados → recomendación; trazabilidad; incertidumbre; viabilidad | Lista de 4 ventajas |
| 4 | Lógica y cláusulas de Horn | Un solo literal positivo; por qué `A ∨ B ⇒ C` se divide (R6a/R6b) | Fórmula de Horn + ejemplo R6 |
| 5 | Base de conocimiento | 11 proposiciones (6 entradas, 3 intermedias, 2 metas) y 7 reglas | Diagrama Mermaid del README |
| 6 | Lógica trivalente | `YES` / `NO` / `UNKNOWN`; ausente ≠ `UNKNOWN`; rol de R4 | Tabla de valores |
| 7 | Arquitectura | KB vs FB; `DevelopmentSubsystem` (experto) y `QuerySubsystem` (usuario); motor del lab05 | Diagrama de bloques |
| 8 | Demo forward | Escenarios 1, 2 y 3 (`forward`); mostrar R3 bloqueada y R4 como respaldo | Captura de salida del notebook |
| 9 | Demo backward | Escenario 4: preguntas solo por datos necesarios y su «¿Por qué?» | Grabación o captura de la interacción |
| 10 | Explicabilidad | «Cómo» con `explain` y «por qué» con `why` | Árbol de prueba indentado |
| 11 | Limitaciones | Conflicto de metas (escenario 5), `resolver_conflicto`, umbrales fijos, sin grados de certeza | Salida del escenario 5 |
| 12 | Conclusiones y futuro | Ventajas de la IA simbólica, trabajo futuro (certeza, difusa, más indicadores), preguntas | Resumen en 3 viñetas |

## Checklist previo a la entrega

- [ ] Ejecutar el notebook completo (`Kernel → Restart & Run All`) sin errores.
- [ ] Verificar que el orden de preguntas del escenario 4 coincide con la diapositiva 9.
- [ ] Agregar a los demás integrantes (si los hay) en el notebook y en la portada.
- [ ] Incluir el aviso legal (no es asesoría financiera) en portada o cierre.
