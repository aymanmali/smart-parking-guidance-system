#include "display_driver.h"

#include <stdio.h>

#ifdef ESP_PLATFORM
#include "driver/gpio.h"
#include "esp_log.h"
static const char *TAG = "SPG_DISP";
#endif

/* Pin mapping matches hardware/kicad SPG-CTRL-v1 PCB */
#define PIN_ARROW_LEFT_G     25
#define PIN_ARROW_LEFT_R     26
#define PIN_ARROW_STRAIGHT_G 27
#define PIN_ARROW_STRAIGHT_R 14
#define PIN_ARROW_RIGHT_G    12
#define PIN_ARROW_RIGHT_R    13

static spg_led_color_t count_to_color(uint16_t count, bool is_open) {
    if (!is_open || count == 0u) {
        return SPG_LED_RED;
    }
    if (count <= 8u) {
        return SPG_LED_AMBER;
    }
    return SPG_LED_GREEN;
}

void spg_display_init(void) {
#ifdef ESP_PLATFORM
    const gpio_config_t io_conf = {
        .pin_bit_mask = (1ULL << PIN_ARROW_LEFT_G) | (1ULL << PIN_ARROW_LEFT_R) |
                        (1ULL << PIN_ARROW_STRAIGHT_G) | (1ULL << PIN_ARROW_STRAIGHT_R) |
                        (1ULL << PIN_ARROW_RIGHT_G) | (1ULL << PIN_ARROW_RIGHT_R),
        .mode = GPIO_MODE_OUTPUT,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE,
    };
    gpio_config(&io_conf);
    ESP_LOGI(TAG, "Display MOSFET output channels initialized");
#endif
}

void spg_display_apply_intersection(
    const spg_intersection_payload_t *payload,
    spg_intersection_hw_state_t *hw_state
) {
    if (payload == NULL || hw_state == NULL) {
        return;
    }
    hw_state->offline_fallback = false;
    hw_state->left_count = payload->left_free;
    hw_state->straight_count = payload->straight_free;
    hw_state->right_count = payload->right_free;

    if (payload->emergency) {
        hw_state->left_arrow = SPG_LED_RED;
        hw_state->straight_arrow = SPG_LED_RED;
        hw_state->right_arrow = SPG_LED_RED;
        return;
    }

    hw_state->left_arrow = count_to_color(payload->left_free, payload->left_open);
    hw_state->straight_arrow = count_to_color(payload->straight_free, payload->straight_open);
    hw_state->right_arrow = count_to_color(payload->right_free, payload->right_open);
}

void spg_display_apply_offline_fallback(spg_intersection_hw_state_t *hw_state) {
    if (hw_state == NULL) {
        return;
    }
    hw_state->offline_fallback = true;
    hw_state->left_arrow = SPG_LED_AMBER;
    hw_state->straight_arrow = SPG_LED_AMBER;
    hw_state->right_arrow = SPG_LED_AMBER;
}

void spg_display_flush_gpio(const spg_intersection_hw_state_t *hw_state) {
    if (hw_state == NULL) {
        return;
    }
#ifdef ESP_PLATFORM
    gpio_set_level(PIN_ARROW_LEFT_G, hw_state->left_arrow == SPG_LED_GREEN || hw_state->left_arrow == SPG_LED_AMBER);
    gpio_set_level(PIN_ARROW_LEFT_R, hw_state->left_arrow == SPG_LED_RED || hw_state->left_arrow == SPG_LED_AMBER);
    gpio_set_level(PIN_ARROW_STRAIGHT_G, hw_state->straight_arrow == SPG_LED_GREEN || hw_state->straight_arrow == SPG_LED_AMBER);
    gpio_set_level(PIN_ARROW_STRAIGHT_R, hw_state->straight_arrow == SPG_LED_RED || hw_state->straight_arrow == SPG_LED_AMBER);
    gpio_set_level(PIN_ARROW_RIGHT_G, hw_state->right_arrow == SPG_LED_GREEN || hw_state->right_arrow == SPG_LED_AMBER);
    gpio_set_level(PIN_ARROW_RIGHT_R, hw_state->right_arrow == SPG_LED_RED || hw_state->right_arrow == SPG_LED_AMBER);
#else
    (void)hw_state;
#endif
}
