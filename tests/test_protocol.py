"""Tests for RS-485 binary protocol framing and CRC-16/MODBUS."""

import pytest

from backend.protocol import (
    CMD_ENTRANCE_UPDATE,
    CMD_INTERSECTION_UPDATE,
    crc16_modbus,
    decode_frame,
    encode_entrance_frame,
    encode_intersection_frame,
)


def test_crc16_modbus_standard_vector():
    # Standard Modbus test vector: ASCII "123456789" -> 0x4B37
    assert crc16_modbus(b"123456789") == 0x4B37


def test_entrance_frame_roundtrip():
    frame = encode_entrance_frame(addr=1, total_free=142, zone_free=[40, 32, 45, 25], is_open=True)
    decoded = decode_frame(frame)
    assert decoded["addr"] == 1
    assert decoded["cmd"] == CMD_ENTRANCE_UPDATE
    assert decoded["crc_ok"] is True
    assert decoded["data"]["total_free"] == 142
    assert decoded["data"]["zone_free"] == [40, 32, 45, 25]
    assert decoded["data"]["is_open"] is True


def test_intersection_frame_roundtrip():
    frame = encode_intersection_frame(addr=11, left_free=0, straight_free=88, right_free=27)
    decoded = decode_frame(frame)
    assert decoded["addr"] == 11
    assert decoded["cmd"] == CMD_INTERSECTION_UPDATE
    assert decoded["data"]["left_free"] == 0
    assert decoded["data"]["left_open"] is False
    assert decoded["data"]["straight_free"] == 88
    assert decoded["data"]["straight_open"] is True
    assert decoded["data"]["right_free"] == 27
    assert decoded["data"]["right_open"] is True


def test_corrupted_crc_rejected():
    frame = bytearray(encode_intersection_frame(addr=12, left_free=10, straight_free=20, right_free=30))
    frame[6] ^= 0xFF  # Flip bits in payload
    with pytest.raises(ValueError, match="CRC mismatch"):
        decode_frame(bytes(frame))
