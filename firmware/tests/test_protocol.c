#include "../main/display_driver.h"
#include "../main/rs485_protocol.h"

#include <assert.h>
#include <stdio.h>
#include <string.h>

static void test_crc16_vector(void) {
    const uint8_t vec[] = "123456789";
    uint16_t crc = spg_crc16_modbus(vec, 9u);
    assert(crc == 0x4B37u);
}

static void test_intersection_decode_and_driver(void) {
    /* Build frame matching backend/protocol.py: addr=11, cmd=0x02, L=0, S=88, R=5, flags=0x06 */
    uint8_t frame[14] = {
        0xAAu, 0x55u,       /* SOF */
        11u,                /* ADDR */
        0x02u,              /* CMD_INTERSECTION_UPDATE */
        7u,                 /* LEN */
        0x00u, 0x00u,       /* left_free = 0 */
        0x00u, 0x58u,       /* straight_free = 88 */
        0x00u, 0x05u,       /* right_free = 5 (<=8 -> AMBER) */
        0x06u,              /* flags: straight_open | right_open */
        0x00u, 0x00u        /* CRC placeholder */
    };
    uint16_t crc = spg_crc16_modbus(&frame[2], 10u);
    frame[12] = (uint8_t)(crc & 0xFFu);
    frame[13] = (uint8_t)((crc >> 8) & 0xFFu);

    spg_frame_t decoded;
    assert(spg_decode_frame(frame, sizeof(frame), &decoded) == SPG_OK);
    assert(decoded.addr == 11u);
    assert(decoded.cmd == SPG_CMD_INTERSECTION_UPDATE);
    assert(decoded.data.intersection.left_free == 0u);
    assert(decoded.data.intersection.straight_free == 88u);
    assert(decoded.data.intersection.right_free == 5u);
    assert(!decoded.data.intersection.left_open);
    assert(decoded.data.intersection.straight_open);
    assert(decoded.data.intersection.right_open);

    spg_intersection_hw_state_t hw;
    spg_display_apply_intersection(&decoded.data.intersection, &hw);
    assert(hw.left_arrow == SPG_LED_RED);
    assert(hw.straight_arrow == SPG_LED_GREEN);
    assert(hw.right_arrow == SPG_LED_AMBER);
    assert(!hw.offline_fallback);

    /* Corrupt 1 byte -> must fail CRC */
    frame[7] ^= 0xFFu;
    assert(spg_decode_frame(frame, sizeof(frame), &decoded) == SPG_ERR_BAD_CRC);
}

static void test_offline_fallback(void) {
    spg_intersection_hw_state_t hw;
    spg_display_apply_offline_fallback(&hw);
    assert(hw.offline_fallback);
    assert(hw.left_arrow == SPG_LED_AMBER);
    assert(hw.straight_arrow == SPG_LED_AMBER);
    assert(hw.right_arrow == SPG_LED_AMBER);
}

int main(void) {
    test_crc16_vector();
    test_intersection_decode_and_driver();
    test_offline_fallback();
    printf("All ESP32 Embedded C firmware unit tests PASSED!\n");
    return 0;
}
