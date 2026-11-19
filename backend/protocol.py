"""RS-485 binary wire protocol encoder/decoder with CRC-16/MODBUS.

Frame layout (bit-for-bit compatible with firmware/main/rs485_protocol.c):
  [0..1]   SOF     : 0xAA, 0x55
  [2]      ADDR    : Node RS-485 address (1..247, 0xFF broadcast)
  [3]      CMD     : 0x01=Entrance Update, 0x02=Intersection Update, 0x03=Heartbeat
  [4]      LEN     : Payload length in bytes
  [5..N-3] PAYLOAD : Packed big-endian values
  [N-2..N-1] CRC16 : CRC-16/MODBUS over ADDR..PAYLOAD (little-endian)
"""

from __future__ import annotations

import struct

SOF = b"\xaa\x55"
CMD_ENTRANCE_UPDATE = 0x01
CMD_INTERSECTION_UPDATE = 0x02
CMD_HEARTBEAT = 0x03


def crc16_modbus(data: bytes) -> int:
    """Compute standard CRC-16/MODBUS (poly 0xA001, init 0xFFFF)."""
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc & 0xFFFF


def _pack_frame(addr: int, cmd: int, payload: bytes) -> bytes:
    if not (0 <= addr <= 0xFF):
        raise ValueError(f"RS-485 address out of range: {addr}")
    if len(payload) > 64:
        raise ValueError(f"Payload exceeds 64 bytes: {len(payload)}")
    body = bytes([addr, cmd, len(payload)]) + payload
    crc = crc16_modbus(body)
    return SOF + body + struct.pack("<H", crc)


def _clamp_u16(value: int) -> int:
    """Clamp a counter to the unsigned 16-bit wire range [0, 65535]."""
    return min(0xFFFF, max(0, value))


def encode_entrance_frame(
    addr: int,
    total_free: int,
    zone_free: list[int],
    is_open: bool = True,
) -> bytes:
    """Encode CMD=0x01 entrance sign update (11 bytes payload).

    Payload: total_free (u16 BE), z0..z3 (4 x u16 BE), flags (u8: bit0=open).
    """
    padded = (zone_free + [0, 0, 0, 0])[:4]
    flags = 0x01 if is_open else 0x00
    payload = struct.pack(
        ">HHHHHB",
        _clamp_u16(total_free),
        _clamp_u16(padded[0]),
        _clamp_u16(padded[1]),
        _clamp_u16(padded[2]),
        _clamp_u16(padded[3]),
        flags,
    )
    return _pack_frame(addr, CMD_ENTRANCE_UPDATE, payload)


def encode_intersection_frame(
    addr: int,
    left_free: int,
    straight_free: int,
    right_free: int,
    emergency: bool = False,
) -> bytes:
    """Encode CMD=0x02 intersection directional sign update (7 bytes payload).

    Payload: left (u16 BE), straight (u16 BE), right (u16 BE), flags (u8).
    Flags: bit0=left_open, bit1=straight_open, bit2=right_open, bit7=emergency.
    """
    flags = 0
    if left_free > 0:
        flags |= 0x01
    if straight_free > 0:
        flags |= 0x02
    if right_free > 0:
        flags |= 0x04
    if emergency:
        flags |= 0x80
    payload = struct.pack(
        ">HHHB",
        _clamp_u16(left_free),
        _clamp_u16(straight_free),
        _clamp_u16(right_free),
        flags,
    )
    return _pack_frame(addr, CMD_INTERSECTION_UPDATE, payload)


def decode_frame(frame: bytes) -> dict:
    """Validate SOF + CRC-16 and decode a binary RS-485 frame."""
    if len(frame) < 7:
        raise ValueError("Frame too short")
    if frame[:2] != SOF:
        raise ValueError(f"Invalid SOF: {frame[:2].hex()}")

    addr = frame[2]
    cmd = frame[3]
    length = frame[4]
    expected_len = 5 + length + 2
    if len(frame) != expected_len:
        raise ValueError(f"Frame length mismatch: got {len(frame)}, expected {expected_len}")

    body = frame[2 : 5 + length]
    rx_crc = struct.unpack("<H", frame[-2:])[0]
    calc_crc = crc16_modbus(body)
    if rx_crc != calc_crc:
        raise ValueError(f"CRC mismatch: rx=0x{rx_crc:04X}, calc=0x{calc_crc:04X}")

    payload = frame[5 : 5 + length]
    result: dict = {"addr": addr, "cmd": cmd, "length": length, "crc_ok": True}

    if cmd == CMD_ENTRANCE_UPDATE and length == 11:
        total, z0, z1, z2, z3, flags = struct.unpack(">HHHHHB", payload)
        result["data"] = {
            "total_free": total,
            "zone_free": [z0, z1, z2, z3],
            "is_open": bool(flags & 0x01),
        }
    elif cmd == CMD_INTERSECTION_UPDATE and length == 7:
        left, straight, right, flags = struct.unpack(">HHHB", payload)
        result["data"] = {
            "left_free": left,
            "straight_free": straight,
            "right_free": right,
            "left_open": bool(flags & 0x01),
            "straight_open": bool(flags & 0x02),
            "right_open": bool(flags & 0x04),
            "emergency": bool(flags & 0x80),
        }
    else:
        result["raw_payload"] = payload.hex()

    return result
