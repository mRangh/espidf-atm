/*
 * ============================================================================
 * @repo        espidf-atm
 *
 * @author      Marco Antônio Ranghetti
 * @github      github.com/mRangh
 * @email       marcoantonioranghetti@gmail.com
 * @academic    d2026008956@unifei.edu.br
 *
 * @version     1.0.0
 * @date        2026-07-05
 * @license     Apache License 2.0
 * ============================================================================
 */

#ifndef UART_HANDLER_HPP
#define UART_HANDLER_HPP

#include <cstdio>
#include <string>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/uart.h"
#include "esp_log.h"
#include "atm_ctrl.hpp"

#define UART_COMM_NUM UART_NUM_0
#define UART_BUF_SIZE (1024)

static const char *UART_TAG = "UART_COMM";

enum msg {
    Deposit_msg,
    Withdraw_msg,
    msg_unknown,
};

inline msg parse_msg(const char* raw, uint8_t& value) {
    char cmd[16] = {0};
    int num = -1;

    int parsed = sscanf(raw, "%15s %d", cmd, &num);

    if (parsed < 1) return msg_unknown;

    if (strcmp(cmd, "DEPOSIT") == 0) {
        if (parsed < 2 || num < 0 || num > 255) return msg_unknown;
        value = static_cast<uint8_t>(num);
        return Deposit_msg;
    }

    if (strcmp(cmd, "WITHDRAW") == 0) {
        if (parsed < 2 || num < 0 || num > 255) return msg_unknown;
        value = static_cast<uint8_t>(num);
        return Withdraw_msg;
    }

    return msg_unknown;
}

static inline void uart_rx_task(void *pvParameters){

    ATM* atm_inst = static_cast<ATM*>(pvParameters);

    if (atm_inst == nullptr){
        ESP_LOGE(UART_TAG, "Invalid ATM instance\n");
        vTaskDelete(NULL);
        return;
    }

    uint8_t* data = (uint8_t*) malloc(UART_BUF_SIZE);
    if (data == nullptr) {
        ESP_LOGE(UART_TAG, "Failed to allocate UART buffer");
        vTaskDelete(NULL);
        return;
    }

    while(true) {
        int len = uart_read_bytes(UART_COMM_NUM, data, UART_BUF_SIZE - 1, pdMS_TO_TICKS(20));

        if (len > 0) {
            data[len] = '\0';

            while (len > 0 && (data[len - 1] == '\n' || data[len - 1] == '\r')) {
                data[--len] = '\0';
            }

            uint8_t coin_num;
            msg cmd = parse_msg((char*) data, coin_num);

            switch(cmd) {

                case Deposit_msg:
                    atm_inst->do_deposit(coin_num);
                    break;

                case Withdraw_msg:
                    atm_inst->do_withdraw(coin_num);
                    break;

                case msg_unknown:
                    break;
            }
        }
    }

    free(data);
    vTaskDelete(NULL);
}

inline void init_uart_communication(ATM& atm, int core_id) {
    uart_config_t uart_config = {};
    uart_config.baud_rate           = 115200;
    uart_config.data_bits           = UART_DATA_8_BITS;
    uart_config.parity              = UART_PARITY_DISABLE;
    uart_config.stop_bits           = UART_STOP_BITS_1;
    uart_config.flow_ctrl           = UART_HW_FLOWCTRL_DISABLE;
    uart_config.rx_flow_ctrl_thresh = 0;
    uart_config.source_clk          = UART_SCLK_DEFAULT;

    ESP_ERROR_CHECK(uart_param_config(UART_COMM_NUM, &uart_config));
    ESP_ERROR_CHECK(uart_driver_install(UART_COMM_NUM, UART_BUF_SIZE * 2, 0, 0, NULL, 0));

    xTaskCreatePinnedToCore(
        uart_rx_task,
        "uart_rx_task",
        3072,
        &atm,
        5,
        NULL,
        core_id
    );

    ESP_LOGI(UART_TAG, "Successful init on Core %d.", core_id);
}

#endif
