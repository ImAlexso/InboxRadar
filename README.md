# InboxRadar

InboxRadar es una aplicación local de escritorio para Windows que detecta correos de Outlook que requieren atención y los mantiene pendientes hasta que el usuario toma una decisión explícita.

> Outlook avisa de que ha llegado algo. InboxRadar recuerda que todavía queda algo por hacer.

## El problema

El flujo habitual del correo es sencillo:

```text
Llega un correo
    ↓
Aparece una notificación
    ↓
El usuario lo abre
    ↓
"Lo hago luego"
    ↓
El correo queda leído o archivado
    ↓
La acción pendiente se olvida
```

InboxRadar separa dos conceptos:

```text
ESTADO DEL BUZÓN
- leído / no leído
- dentro / fuera del Inbox

ESTADO FUNCIONAL
- pendiente
- gestionado
- ignorado
```

Un correo puede seguir pendiente aunque:

- ya se haya leído;
- se haya archivado;
- haya salido del Inbox;
- la notificación original de Outlook haya desaparecido.

Solo deja de estar pendiente cuando el usuario decide:

- **Gestionado**: la acción requerida ya se ha completado.
- **Ignorar**: el correo no debe seguir tratándose como pendiente.

InboxRadar no intenta sustituir Outlook ni sus notificaciones. El objetivo es evitar que una acción pendiente desaparezca junto con la notificación.

---

## Estado actual

El MVP implementa el ciclo completo:

```text
Microsoft 365 / Outlook
        ↓
Microsoft Graph Delta
        ↓
Clasificación determinista
        ↓
Seguimiento local seguro
        ↓
Sincronización automática
        ↓
Tray icon + popup
        ↓
Abrir / Gestionado / Ignorar
```

Funcionalidades actuales:

- autenticación OAuth mediante Microsoft Entra;
- Microsoft Graph con permisos delegados mínimos;
- sincronización incremental mediante Graph Delta;
- baseline inicial sin importar el histórico como pendientes;
- detección automática de nuevos correos relevantes;
- persistencia local segura;
- seguimiento independiente del estado leído/no leído;
- seguimiento de correos que salen del Inbox;
- sincronización automática en segundo plano;
- aplicación residente en la bandeja del sistema;
- popup para nuevos pendientes;
- cola de alertas;
- apertura del correo original en Outlook;
- acciones `Gestionado` e `Ignorar`;
- reintentos progresivos ante fallos temporales;
- una única instancia de la aplicación;
- navegador configurable para desarrollo o demo.

---

## Arquitectura

InboxRadar se ejecuta completamente en el equipo del usuario.

```text
Microsoft 365 / Exchange
        ↓ HTTPS
Microsoft Graph
        ↓
InboxRadar local en Windows
        ↓
SQLite local + Windows DPAPI
```

No existe backend propio.

El MVP no utiliza:

- Azure Functions;
- App Service;
- Azure SQL;
- Storage Accounts;
- Key Vault;
- servidores propios;
- telemetría externa;
- servicios SaaS de terceros;
- modelos de IA externos.

**Coste incremental de infraestructura del MVP: 0 €.**

### Capas principales

```text
PySide6 UI
    ↓
ApplicationService
    ↓
┌───────────────────────┐
│                       │
sync_engine          database
    ↓                   ↓
Graph Delta       SQLite + DPAPI
```

La interfaz gráfica no accede directamente a:

- Microsoft Graph;
- SQLite;
- DPAPI;
- el cursor Delta.

La frontera principal de la aplicación es `ApplicationService`.

---

## Seguridad y privacidad

La seguridad local es un criterio de diseño del proyecto.

### Permisos de Microsoft Graph

El permiso delegado actual es exclusivamente:

```text
Mail.ReadBasic
```

InboxRadar no solicita:

```text
Mail.Read
Mail.ReadWrite
Mail.Send
Application permissions
```

La aplicación es un **Public Client** y no utiliza `Client Secret`.

### Datos solicitados a Graph

La sincronización solicita únicamente:

```text
id
subject
receivedDateTime
from
isRead
webLink
```

No solicita:

```text
body
bodyPreview
attachments
```

Por tanto, la aplicación no depende de una promesa de "no leer el cuerpo": el token actual no tiene permiso para hacerlo.

### Protección local

El estado local se almacena en:

```text
%LOCALAPPDATA%\InboxRadar\
```

La base de datos utiliza SQLite.

Los datos sensibles se protegen con:

```text
Windows DPAPI
Current User
```

Se protegen localmente:

- asunto;
- nombre del remitente;
- dirección del remitente;
- fecha de recepción;
- webLink;
- cursor Delta.

El ID real del mensaje no se almacena como identificador local:

```text
message_id
    ↓
SHA-256
    ↓
message_key
```

Las referencias de diagnóstico utilizan una referencia segura corta derivada del hash.

Se mantienen en claro únicamente estados técnicos o funcionales:

```text
is_read
classification
attention_status
mailbox_status
created_at
updated_at
```

---

## Modelo funcional

### Clasificación

El MVP utiliza una clasificación sencilla y determinista basada en el asunto.

Actualmente reconoce marcadores como:

```text
action required
requires action
approval required
requiere una acción
acción requerida
```

El objetivo del MVP no es demostrar un clasificador perfecto, sino el ciclo completo:

```text
detectar
→ mantener pendiente
→ alertar
→ resolver
```

La definición de reglas corporativas reales se considera una fase posterior.

### Estados de atención

```text
PENDING
MANAGED
IGNORED
```

Transiciones permitidas:

```text
PENDING → MANAGED
PENDING → IGNORED
```

Una vez resuelto, el mensaje no cambia entre estados terminales.

### Estado del buzón

```text
IN_INBOX
REMOVED_FROM_INBOX
```

El estado del buzón no decide si el correo sigue pendiente.

Por tanto:

```text
correo leído
→ puede seguir PENDING

correo archivado
→ puede seguir PENDING
```

---

## Sincronización incremental

InboxRadar utiliza Microsoft Graph Delta sobre:

```text
/me/mailFolders/inbox/messages/delta
```

y solicita:

```text
Prefer: IdType="ImmutableId"
```

### Primera ejecución

La primera sincronización crea un baseline desde el momento actual.

```text
histórico anterior
→ no se importa como pendiente

cambios posteriores
→ sí se procesan
```

### Ejecuciones posteriores

```text
deltaLink persistido
        ↓
seguir cursor
        ↓
procesar cambios
        ↓
guardar nuevo deltaLink
```

El nuevo cursor solo se guarda después de completar el procesamiento.

Si el procesamiento falla:

```text
el cursor no avanza
```

La siguiente sincronización puede repetir eventos, pero el procesamiento es idempotente.

---

## Sincronización automática

La aplicación sincroniza en segundo plano:

```text
arranque
    ↓
sync inmediata
    ↓
esperar 60 segundos
    ↓
nueva sync
```

La operación de red no se ejecuta en el hilo gráfico.

La implementación utiliza:

```text
QTimer
QThreadPool
QRunnable
```

La aplicación:

- no bloquea la interfaz durante la sincronización;
- evita sincronizaciones simultáneas;
- mantiene un único worker activo;
- aplica backoff progresivo ante errores temporales.

Actualmente:

```text
1.er fallo temporal → 60 s
2.º fallo temporal  → 120 s
3.er fallo temporal → 240 s
máximo              → 5 min
```

---

## Aplicación residente

Cuando la bandeja del sistema está disponible:

```text
cerrar la ventana con X
→ oculta la ventana
→ InboxRadar sigue ejecutándose
```

Desde el tray se puede:

- abrir InboxRadar;
- consultar el número de pendientes;
- ver el estado de sincronización;
- sincronizar manualmente;
- salir completamente.

Si la bandeja no está disponible, cerrar la ventana termina la aplicación normalmente.

---

## Alertas

Cuando una sincronización detecta un nuevo correo relevante:

```text
TRACKED_NEW_MESSAGE
        ↓
message_key segura
        ↓
AlertManager
        ↓
popup
```

El popup permite:

- abrir el correo;
- marcarlo como gestionado;
- ignorarlo;
- cerrarlo sin resolver el pendiente.

Si llegan varios mensajes:

```text
popup 1
    ↓
termina
    ↓
popup 2
```

No se muestran múltiples alertas superpuestas.

---

## Instancia única

InboxRadar evita ejecutar varias instancias simultáneamente.

La implementación combina:

```text
QLockFile
+
QLocalServer / QLocalSocket
```

Si se intenta abrir InboxRadar de nuevo:

```text
segunda ejecución
    ↓
detecta la instancia existente
    ↓
solicita reactivar la ventana
    ↓
termina
```

Esto evita:

- varios iconos de tray;
- polling duplicado;
- popups duplicados;
- conflictos innecesarios sobre SQLite.

---

## Requisitos

Actualmente:

```text
Windows
Python 3.12
Cuenta Microsoft personal para el laboratorio
```

Entorno de desarrollo validado:

```text
Python 3.12.10
```

---

## Configuración de Microsoft Entra

La App Registration actual del laboratorio utiliza:

```text
Nombre:
InboxRadar Lab

Tipo de cuenta:
Personal Microsoft accounts only

Redirect URI:
http://localhost

Allow public client flows:
Yes
```

Permiso delegado:

```text
Microsoft Graph
Mail.ReadBasic
```

No debe configurarse:

- Client Secret;
- permisos de aplicación;
- `Mail.ReadWrite`;
- `Mail.Send`.

---

## Preparar el proyecto

Desde PowerShell:

```powershell
cd C:\FutureSpace\Proyectos\InboxRadar

py -3.12 -m venv .venv

Set-ExecutionPolicy `
    -Scope Process `
    -ExecutionPolicy Bypass

.\.venv\Scripts\Activate.ps1

python -m pip install -e .

Copy-Item .env.example .env
```

Configura:

```text
CLIENT_ID=<application-client-id>
AUTHORITY_TENANT=consumers
```

Para un tenant corporativo:

```text
AUTHORITY_TENANT=<tenant-id>
```

---

## Navegador

Opcionalmente se puede forzar el navegador utilizado al abrir un correo:

```text
INBOX_RADAR_BROWSER_PATH=C:/Program Files/Google/Chrome/Application/chrome.exe
```

Si no se configura, se utiliza el navegador predeterminado del sistema.

Esta opción existe principalmente para desarrollo y demostraciones.

---

## Ejecutar la aplicación

```powershell
inbox-radar
```

La aplicación:

1. inicia la interfaz;
2. recupera el estado local;
3. sincroniza en segundo plano;
4. permanece activa en el tray;
5. continúa sincronizando periódicamente.

---

## CLI de diagnóstico

También existe una CLI fina:

```powershell
inbox-radar-spike
```

Se utiliza para validar la sincronización sin arrancar la interfaz.

La salida evita imprimir datos sensibles.

Ejemplo:

```text
SYNC_START

EVENT result=TRACKED_NEW_MESSAGE ref=e1487322f2b1

DELTA_SYNC_DONE changes=3 pending=1
```

No imprime:

- asuntos;
- remitentes;
- direcciones;
- IDs reales;
- webLinks;
- JSON de Graph;
- tokens.

---

## Self-test

El proyecto incluye:

```powershell
python -m inbox_radar.poc_selftest
```

Actualmente valida:

- correo irrelevante no persistido;
- mensaje ACTION persistido;
- idempotencia;
- eventos duplicados;
- actualización parcial de `isRead`;
- `isRead` duplicado ignorado;
- salida del Inbox;
- salida repetida;
- restauración al Inbox;
- cursor Delta protegido;
- ausencia de datos sensibles en SQLite;
- una única fila por mensaje;
- consulta de pendientes;
- consulta exacta mediante `message_key`;
- transición a gestionado;
- protección frente a cambios de estado terminal;
- contrato seguro entre sync y aplicación.

Resultado esperado:

```text
SELFTEST_PASS checks=security,idempotence,lifecycle
```

---

## Estructura del proyecto

```text
src/inbox_radar/
├── application.py
├── auth.py
├── config.py
├── database.py
├── delta_state.py
├── errors.py
├── graph.py
├── message_processor.py
├── sync_engine.py
├── sync_controller.py
├── alert_manager.py
├── single_instance.py
├── windows_protection.py
├── desktop.py
├── spike.py
├── poc_selftest.py
└── ui/
    ├── main_window.py
    ├── pending_card.py
    ├── alert_popup.py
    ├── tray_icon.py
    ├── app_icon.py
    └── theme.py
```

---

## Limitaciones actuales del MVP

El estado actual es un MVP, no un producto corporativo terminado.

Limitaciones deliberadas:

- clasificación basada en reglas simples del asunto;
- configuración mediante `.env`;
- sin instalador;
- sin empaquetado `.exe`;
- sin inicio automático con Windows;
- sin actualización automática;
- sin logging local estructurado;
- sin panel de configuración;
- sin telemetría;
- sin backend central;
- validado actualmente con una cuenta Microsoft personal.

Estas limitaciones no bloquean la demostración del valor funcional.

---

## Posible transición corporativa

La arquitectura busca que la transición sea principalmente de configuración:

```text
MVP PERSONAL
CLIENT_ID personal
AUTHORITY_TENANT=consumers

FUTURO CORPORATIVO
CLIENT_ID corporativo
AUTHORITY_TENANT=<tenant-id>
```

El objetivo es conservar:

- motor de sincronización;
- SQLite;
- DPAPI;
- procesador;
- `ApplicationService`;
- UI.

Antes de un piloto corporativo habría que validar:

- App Registration corporativa;
- consentimiento de permisos;
- políticas de Conditional Access;
- definición real de correos accionables;
- logging local seguro;
- empaquetado e instalación;
- inicio con Windows;
- estrategia de actualización.

---

## Demo recomendada

La demostración más clara del producto es:

```text
1. Enviar un correo ACTION
2. Esperar a que InboxRadar lo detecte
3. Abrirlo
4. Marcarlo como leído
5. Archivarlo en Outlook
6. Comprobar que sigue pendiente
7. Marcarlo como Gestionado
8. Comprobar que desaparece
```

La idea que demuestra es:

> Leer o archivar un correo no significa que la acción asociada esté resuelta.

---

## Filosofía del proyecto

InboxRadar no intenta copiar Outlook.

Outlook sigue siendo la fuente real del correo.

InboxRadar mantiene únicamente una capa local de atención:

```text
¿Este correo todavía requiere una decisión?
```

La definición más corta del producto es:

> Outlook avisa de que ha llegado algo. InboxRadar recuerda que todavía queda algo por hacer.
