from __future__ import annotations


from datetime import UTC, datetime
from typing import Any

from .auth import AuthService
from .config import load_settings
from .database import initialize_database
from .delta_state import load_delta_link, save_delta_link
from .errors import InboxRadarError
from .graph import GraphClient
from .message_processor import process_message_event


def _sender_name(message: dict[str, Any]) -> str:
    sender = (message.get("from") or {}).get("emailAddress") or {}
    return sender.get("name") or sender.get("address") or "Desconocido"


def _print_message(message: dict[str, Any]) -> None:
    removed = message.get("@removed")
    if removed:
        print(f"  - [ELIMINADO] {message.get('id', 'sin id')}")
        return

    subject = message.get("subject") or "(sin asunto)"
    received = message.get("receivedDateTime") or "sin fecha"
    read_state = "leído" if message.get("isRead") else "NO LEÍDO"
    preview = (message.get("bodyPreview") or "").replace("\r", " ").replace("\n", " ")
    preview = preview[:160] + ("…" if len(preview) > 160 else "")

    print(f"  - {received} | {read_state} | {_sender_name(message)}")
    print(f"    {subject}")
    if preview:
        print(f"    {preview}")


def _drain_delta(client: GraphClient, first_page) -> tuple[list[dict[str, Any]], str]:
    changes: list[dict[str, Any]] = []
    page = first_page

    while True:
        changes.extend(page.messages)

        if page.next_link:
            page = client.follow_delta_link(page.next_link)
            continue

        if page.delta_link:
            return changes, page.delta_link

        raise RuntimeError("La respuesta delta no contiene nextLink ni deltaLink.")


def run() -> None:
    initialize_database()
    settings = load_settings()
    token = AuthService(settings).get_access_token()
    client = GraphClient(token)

    print("\n[1/2] Acceso al buzón confirmado. Últimos 5 mensajes:")
    for message in client.list_recent_messages(top=5):
        _print_message(message)

    saved_link = load_delta_link()

    if not saved_link:
        cutoff = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        print("\n[2/2] No hay cursor delta todavía.")
        print(f"Inicializando desde {cutoff}; el histórico anterior no se importa.")
        first_page = client.start_delta(cutoff)
        changes, delta_link = _drain_delta(client, first_page)
        save_delta_link(delta_link)
        print(f"Cursor creado. Cambios vistos durante el baseline: {len(changes)} (sin notificar).")
        print("Ejecuta el comando otra vez después de recibir o leer un correo.")
        return

    print("\n[2/2] Consultando cambios desde el último cursor...")
    first_page = client.follow_delta_link(saved_link)
    changes, delta_link = _drain_delta(client, first_page)

    if not changes:
        save_delta_link(delta_link)
        print("Sin cambios desde la última ejecución.")
        return

    print(f"Cambios detectados: {len(changes)}")
    for message in changes:
        result = process_message_event(message)
        print(f"- {result}: {message.get('id', '<sin id>')}")
        _print_message(message)

    save_delta_link(delta_link)



def main() -> None:
    try:
        run()
    except InboxRadarError as exc:
        raise SystemExit(f"\nERROR: {exc}") from exc
    except KeyboardInterrupt:
        raise SystemExit("\nCancelado por el usuario.") from None


if __name__ == "__main__":
    main()
