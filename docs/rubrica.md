# Rúbrica de evaluación — reto «Memories»

Corrección **automática**: los 4 tests de los notebooks `03` (alumno) y `04` (solución) son el único mecanismo de evaluación. No se pide memoria escrita ni revisión manual de estilo.

| # | Criterio | Qué se comprueba | Test que lo evalúa | Resultado |
|---|----------|------------------|--------------------|-----------|
| C1 | Registro y recuperación de mensajes | Los mensajes se guardan en la sesión indicada y se recuperan con su `role` y `content` completos; una sesión sin mensajes devuelve `[]` | `test_c1_registro_y_recuperacion` | ✅ / ❌ |
| C2 | Orden correcto del historial | Varios mensajes seguidos se devuelven en orden cronológico, tal y como se insertaron | `test_c2_orden_del_historial` | ✅ / ❌ |
| C3 | Aislamiento entre sesiones | Cada sesión solo ve sus mensajes; una sesión nueva no tiene historial ajeno | `test_c3_aislamiento_entre_sesiones` | ✅ / ❌ |
| C4 | Borrado independiente de una sesión | Al borrar una sesión queda vacía y las demás conservan su historial | `test_c4_borrado_independiente` | ✅ / ❌ |

**Escala:** 4/4 superado · 3/4 casi (repasar el criterio fallido con las pistas del notebook) · 0-2/4 no superado.

**Evidencia:** la celda final del notebook imprime `🎉 ¡TODAS LAS PRUEBAS SUPERADAS! (4/4)` o el detalle de los tests fallidos con su mensaje de `assert`. El formador solo necesita ver esa celda.
