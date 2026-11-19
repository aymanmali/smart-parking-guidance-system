#ifndef SPG_DISPLAY_DRIVER_H
#define SPG_DISPLAY_DRIVER_H

#include "rs485_protocol.h"

#include <stdbool.h>
#include <stdint.h>

typedef enum {
    SPG_LED_OFF = 0,
    SPG_LED_GREEN = 1,
    SPG_LED_AMBER = 2,
    SPG_LED_RED = 3
} spg_led_color_t;

typedef struct {
    spg_led_color_t left_arrow;
    spg_led_color_t straight_arrow;
    spg_led_color_t right_arrow;
    uint16_t left_count;
    uint16_t straight_count;
    uint16_t right_count;
    bool offline_fallback;
} spg_intersection_hw_state_t;

void spg_display_init(void);
void spg_display_apply_intersection(
    const spg_intersection_payload_t *payload,
    spg_intersection_hw_state_t *hw_state
);
void spg_display_apply_offline_fallback(spg_intersection_hw_state_t *hw_state);
void spg_display_flush_gpio(const spg_intersection_hw_state_t *hw_state);

#endif /* SPG_DISPLAY_DRIVER_H */
