/**
 * Smart Parking Guidance & Management System — ESP32 Signage Controller Firmware
 * Target Board: SPG-CTRL-v1 (ESP32-WROOM-32E + RS-485 + 12V/24V MOSFET LED Drivers)
 */

#include "display_driver.h"
#include "rs485_protocol.h"

#ifdef ESP_PLATFORM
#include "driver/gpio.h"
#include "driver/uart.h"
#include "esp_log.h"
#include "esp_task_wdt.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

#define SPG_NODE_RS485_ADDR 11u /* INT-1 default; configurable via DIP switch / NVS */
#define RS485_UART_PORT     UART_NUM_2
#define RS485_TX_PIN        17
#define RS485_RX_PIN        16
#define RS485_RTS_DE_PIN    4
#define RS485_BAUDRATE      115200
#define OFFLINE_TIMEOUT_MS  15000

static const char *TAG = "SPG_MAIN";

static void rs485_init(void) {
    const uart_config_t cfg = {
        .baud_rate = RS485_BAUDRATE,
        .data_bits = UART_DATA_8_BITS,
        .parity = UART_PARITY_DISABLE,
        .stop_bits = UART_STOP_BITS_1,
        .flow_ctrl = UART_HW_FLOWCTRL_DISABLE,
        .source_clk = UART_SCLK_DEFAULT,
    };
    uart_driver_install(RS485_UART_PORT, 256, 256, 0, NULL, 0);
    uart_param_config(RS485_UART_PORT, &cfg);
    uart_set_pin(RS485_UART_PORT, RS485_TX_PIN, RS485_RX_PIN, RS485_RTS_DE_PIN, UART_PIN_NO_CHANGE);
    uart_set_mode(RS485_UART_PORT, UART_MODE_RS485_HALF_DUPLEX);
}

void app_main(void) {
    ESP_LOGI(TAG, "Booting SPG-CTRL-v1 Signage Node (RS-485 addr=%u)", SPG_NODE_RS485_ADDR);
    spg_display_init();
    rs485_init();

    esp_task_wdt_add(NULL);

    spg_intersection_hw_state_t hw_state = {0};
    spg_display_apply_offline_fallback(&hw_state);
    spg_display_flush_gpio(&hw_state);

    uint8_t rx_buf[128];
    TickType_t last_rx_tick = xTaskGetTickCount();

    while (1) {
        esp_task_wdt_reset();

        int n = uart_read_bytes(RS485_UART_PORT, rx_buf, sizeof(rx_buf), pdMS_TO_TICKS(250));
        if (n >= 7) {
            spg_frame_t frame;
            if (spg_decode_frame(rx_buf, (size_t)n, &frame) == SPG_OK) {
                if (frame.addr == SPG_NODE_RS485_ADDR || frame.addr == SPG_ADDR_BROADCAST) {
                    last_rx_tick = xTaskGetTickCount();
                    if (frame.cmd == SPG_CMD_INTERSECTION_UPDATE) {
                        spg_display_apply_intersection(&frame.data.intersection, &hw_state);
                        spg_display_flush_gpio(&hw_state);
                        ESP_LOGI(
                            TAG,
                            "Updated INT sign: L=%u S=%u R=%u",
                            hw_state.left_count,
                            hw_state.straight_count,
                            hw_state.right_count
                        );
                    }
                }
            }
        }

        if ((xTaskGetTickCount() - last_rx_tick) > pdMS_TO_TICKS(OFFLINE_TIMEOUT_MS)) {
            if (!hw_state.offline_fallback) {
                ESP_LOGW(TAG, "Backend timeout — entering amber offline fallback");
                spg_display_apply_offline_fallback(&hw_state);
                spg_display_flush_gpio(&hw_state);
            }
        }
    }
}
#endif
