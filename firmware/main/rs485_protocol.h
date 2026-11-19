#ifndef SPG_RS485_PROTOCOL_H
#define SPG_RS485_PROTOCOL_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#define SPG_SOF_0 0xAAu
#define SPG_SOF_1 0x55u

#define SPG_CMD_ENTRANCE_UPDATE     0x01u
#define SPG_CMD_INTERSECTION_UPDATE 0x02u
#define SPG_CMD_HEARTBEAT           0x03u

#define SPG_ADDR_BROADCAST 0xFFu
#define SPG_MAX_PAYLOAD    64u

typedef struct {
    uint16_t total_free;
    uint16_t zone_free[4];
    bool is_open;
} spg_entrance_payload_t;

typedef struct {
    uint16_t left_free;
    uint16_t straight_free;
    uint16_t right_free;
    bool left_open;
    bool straight_open;
    bool right_open;
    bool emergency;
} spg_intersection_payload_t;

typedef struct {
    uint8_t addr;
    uint8_t cmd;
    uint8_t length;
    union {
        spg_entrance_payload_t entrance;
        spg_intersection_payload_t intersection;
    } data;
} spg_frame_t;

typedef enum {
    SPG_OK = 0,
    SPG_ERR_TOO_SHORT = -1,
    SPG_ERR_BAD_SOF = -2,
    SPG_ERR_BAD_LEN = -3,
    SPG_ERR_BAD_CRC = -4,
    SPG_ERR_UNSUPPORTED_CMD = -5
} spg_status_t;

uint16_t spg_crc16_modbus(const uint8_t *data, size_t len);
spg_status_t spg_decode_frame(const uint8_t *buf, size_t len, spg_frame_t *out);

#endif /* SPG_RS485_PROTOCOL_H */
