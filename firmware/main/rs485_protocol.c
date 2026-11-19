#include "rs485_protocol.h"

#include <string.h>

static uint16_t read_u16_be(const uint8_t *p) {
    return (uint16_t)(((uint16_t)p[0] << 8) | (uint16_t)p[1]);
}

static uint16_t read_u16_le(const uint8_t *p) {
    return (uint16_t)((uint16_t)p[0] | ((uint16_t)p[1] << 8));
}

uint16_t spg_crc16_modbus(const uint8_t *data, size_t len) {
    uint16_t crc = 0xFFFFu;
    for (size_t i = 0; i < len; ++i) {
        crc ^= (uint16_t)data[i];
        for (int bit = 0; bit < 8; ++bit) {
            if (crc & 0x0001u) {
                crc = (uint16_t)((crc >> 1) ^ 0xA001u);
            } else {
                crc >>= 1;
            }
        }
    }
    return crc;
}

spg_status_t spg_decode_frame(const uint8_t *buf, size_t len, spg_frame_t *out) {
    if (buf == NULL || out == NULL || len < 7u) {
        return SPG_ERR_TOO_SHORT;
    }
    if (buf[0] != SPG_SOF_0 || buf[1] != SPG_SOF_1) {
        return SPG_ERR_BAD_SOF;
    }

    uint8_t addr = buf[2];
    uint8_t cmd = buf[3];
    uint8_t payload_len = buf[4];
    size_t expected_len = 5u + (size_t)payload_len + 2u;
    if (payload_len > SPG_MAX_PAYLOAD || len != expected_len) {
        return SPG_ERR_BAD_LEN;
    }

    uint16_t rx_crc = read_u16_le(&buf[5u + payload_len]);
    uint16_t calc_crc = spg_crc16_modbus(&buf[2], 3u + (size_t)payload_len);
    if (rx_crc != calc_crc) {
        return SPG_ERR_BAD_CRC;
    }

    memset(out, 0, sizeof(*out));
    out->addr = addr;
    out->cmd = cmd;
    out->length = payload_len;

    const uint8_t *p = &buf[5];
    if (cmd == SPG_CMD_ENTRANCE_UPDATE && payload_len == 11u) {
        out->data.entrance.total_free = read_u16_be(&p[0]);
        out->data.entrance.zone_free[0] = read_u16_be(&p[2]);
        out->data.entrance.zone_free[1] = read_u16_be(&p[4]);
        out->data.entrance.zone_free[2] = read_u16_be(&p[6]);
        out->data.entrance.zone_free[3] = read_u16_be(&p[8]);
        out->data.entrance.is_open = (p[10] & 0x01u) != 0u;
        return SPG_OK;
    }

    if (cmd == SPG_CMD_INTERSECTION_UPDATE && payload_len == 7u) {
        out->data.intersection.left_free = read_u16_be(&p[0]);
        out->data.intersection.straight_free = read_u16_be(&p[2]);
        out->data.intersection.right_free = read_u16_be(&p[4]);
        uint8_t flags = p[6];
        out->data.intersection.left_open = (flags & 0x01u) != 0u;
        out->data.intersection.straight_open = (flags & 0x02u) != 0u;
        out->data.intersection.right_open = (flags & 0x04u) != 0u;
        out->data.intersection.emergency = (flags & 0x80u) != 0u;
        return SPG_OK;
    }

    if (cmd == SPG_CMD_HEARTBEAT) {
        return SPG_OK;
    }

    return SPG_ERR_UNSUPPORTED_CMD;
}
