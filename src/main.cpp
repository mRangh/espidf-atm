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

#include <esp32_hal.hpp>
#include <esp_log.h>
#include <atm_ctrl.hpp>
#include <uart_handler.hpp>

Servo servo{4};

LM393 coin_counter{13};

atm_config atm_conf {
    //.servo_in     = nullptr,
    .coin_counter_in = coin_counter,
    .servo_coin   = servo,
};

ATM atm{atm_conf};

extern "C" void app_main() {
    init_uart_communication(atm, 0);
    atm.begin(1);
}
