# InboxRadar — Spike 0 (laboratorio personal)

Objetivo: demostrar con una cuenta Outlook/Hotmail personal cuatro cosas antes de construir la aplicación:

1. Login interactivo contra Microsoft Identity.
2. Lectura de `subject`, `bodyPreview`, `isRead` y `webLink` del Inbox.
3. Uso de IDs inmutables de Outlook.
4. Creación y reutilización de un cursor `delta` sin importar el histórico anterior como pendientes.

## 1. Registrar la aplicación en Entra

Crea una nueva App Registration en tu tenant personal:

- **Nombre**: `InboxRadar Lab`
- **Tipos de cuenta**: `Personal Microsoft accounts only`
- No configures ningún client secret.

### Authentication

- Añade plataforma **Mobile and desktop applications**.
- Configura `http://localhost` como redirect URI.
- En **Advanced settings**, activa **Allow public client flows**.

### API permissions

En **API permissions**, elimina `User.Read` si aparece y añade:

- Microsoft Graph
- Delegated permissions
- `Mail.Read`

No añadas `Mail.ReadWrite`, `Mail.Send` ni permisos de aplicación.

Guarda el valor:

- **Application (client) ID**

## 2. Preparar el proyecto

En PowerShell:

```powershell
cd InboxRadar
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e .
Copy-Item .env.example .env
notepad .env
```

Completa:

```text
CLIENT_ID=...
AUTHORITY_TENANT=consumers
```

## 3. Primera ejecución

```powershell
inbox-radar-spike
```

Debe ocurrir lo siguiente:

- Se abre el navegador para iniciar sesión con tu cuenta Outlook/Hotmail personal.
- La app pide `Mail.Read` delegado.
- Se muestran los últimos 5 correos como prueba de lectura.
- Se crea un cursor delta desde el momento actual.
- El histórico anterior no se trata como pendientes.

La caché de autenticación se guarda cifrada por usuario en Windows y el estado local se guarda en:

```text
%LOCALAPPDATA%\InboxRadar\
```

## 4. Segunda prueba

1. Envíate un correo de prueba.
2. Ejecuta de nuevo `inbox-radar-spike`.
3. Debe aparecer como cambio.
4. Ábrelo en Outlook.
5. Ejecuta de nuevo el spike.
6. Debe aparecer la actualización con `isRead = true`.

## Qué NO hace todavía

- No muestra popups.
- No clasifica correos.
- No guarda correos en SQLite.
- No crea pendientes.
- No modifica Outlook.

Es deliberado: primero validamos Graph, permisos, delta e `isRead`.
