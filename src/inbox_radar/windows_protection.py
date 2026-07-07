from __future__ import annotations

import ctypes
import hashlib
import sys
from ctypes import wintypes


CRYPTPROTECT_UI_FORBIDDEN = 0x01
_APP_ENTROPY = b"InboxRadar:v1"
_TEXT_PREFIX = b"InboxRadarText:v1\0"


class _DataBlob(ctypes.Structure):
    _fields_ = [
        ("cbData", wintypes.DWORD),
        ("pbData", ctypes.POINTER(ctypes.c_ubyte)),
    ]


def _require_windows() -> None:
    if sys.platform != "win32":
        raise RuntimeError("Windows DPAPI is required by InboxRadar.")


def _make_blob(data: bytes) -> tuple[_DataBlob, ctypes.Array]:
    buffer = ctypes.create_string_buffer(data)
    blob = _DataBlob(
        cbData=len(data),
        pbData=ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte)),
    )
    return blob, buffer


def _raise_last_windows_error(operation: str) -> None:
    error_code = ctypes.get_last_error()
    raise OSError(
        error_code,
        f"{operation} failed: {ctypes.FormatError(error_code)}",
    )


def _protect_bytes(data: bytes) -> bytes:
    _require_windows()

    crypt32 = ctypes.WinDLL("crypt32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    crypt32.CryptProtectData.argtypes = [
        ctypes.POINTER(_DataBlob),
        wintypes.LPCWSTR,
        ctypes.POINTER(_DataBlob),
        ctypes.c_void_p,
        ctypes.c_void_p,
        wintypes.DWORD,
        ctypes.POINTER(_DataBlob),
    ]
    crypt32.CryptProtectData.restype = wintypes.BOOL

    kernel32.LocalFree.argtypes = [wintypes.HLOCAL]
    kernel32.LocalFree.restype = wintypes.HLOCAL

    input_blob, input_buffer = _make_blob(data)
    entropy_blob, entropy_buffer = _make_blob(_APP_ENTROPY)
    output_blob = _DataBlob()

    _ = input_buffer, entropy_buffer

    success = crypt32.CryptProtectData(
        ctypes.byref(input_blob),
        "InboxRadar",
        ctypes.byref(entropy_blob),
        None,
        None,
        CRYPTPROTECT_UI_FORBIDDEN,
        ctypes.byref(output_blob),
    )

    if not success:
        _raise_last_windows_error("CryptProtectData")

    try:
        return ctypes.string_at(
            output_blob.pbData,
            output_blob.cbData,
        )
    finally:
        kernel32.LocalFree(
            ctypes.cast(output_blob.pbData, wintypes.HLOCAL)
        )


def _unprotect_bytes(data: bytes) -> bytes:
    _require_windows()

    crypt32 = ctypes.WinDLL("crypt32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    crypt32.CryptUnprotectData.argtypes = [
        ctypes.POINTER(_DataBlob),
        ctypes.POINTER(wintypes.LPWSTR),
        ctypes.POINTER(_DataBlob),
        ctypes.c_void_p,
        ctypes.c_void_p,
        wintypes.DWORD,
        ctypes.POINTER(_DataBlob),
    ]
    crypt32.CryptUnprotectData.restype = wintypes.BOOL

    kernel32.LocalFree.argtypes = [wintypes.HLOCAL]
    kernel32.LocalFree.restype = wintypes.HLOCAL

    input_blob, input_buffer = _make_blob(data)
    entropy_blob, entropy_buffer = _make_blob(_APP_ENTROPY)
    output_blob = _DataBlob()

    _ = input_buffer, entropy_buffer

    success = crypt32.CryptUnprotectData(
        ctypes.byref(input_blob),
        None,
        ctypes.byref(entropy_blob),
        None,
        None,
        CRYPTPROTECT_UI_FORBIDDEN,
        ctypes.byref(output_blob),
    )

    if not success:
        _raise_last_windows_error("CryptUnprotectData")

    try:
        return ctypes.string_at(
            output_blob.pbData,
            output_blob.cbData,
        )
    finally:
        kernel32.LocalFree(
            ctypes.cast(output_blob.pbData, wintypes.HLOCAL)
        )


def protect_text(value: str | None) -> bytes | None:
    if value is None:
        return None

    payload = _TEXT_PREFIX + value.encode("utf-8")
    return _protect_bytes(payload)


def unprotect_text(value: bytes | None) -> str | None:
    if value is None:
        return None

    payload = _unprotect_bytes(value)

    if not payload.startswith(_TEXT_PREFIX):
        raise ValueError("Protected text has an unexpected format.")

    return payload[len(_TEXT_PREFIX):].decode("utf-8")


def build_message_key(message_id: str) -> str:
    return hashlib.sha256(
        message_id.encode("utf-8")
    ).hexdigest()


def build_message_ref(message_id: str | None) -> str:
    if not isinstance(message_id, str) or not message_id:
        return "no-id"

    return build_message_key(message_id)[:12]
