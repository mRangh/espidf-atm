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

#ifndef ATM_CTRL_HPP
#define ATM_CTRL_HPP
#include <atomic>
#include <esp32_hal.hpp>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_log.h"
#include "esp_timer.h"

static const char *TAG_I = "SYSTEM";
static const char *TAG_D = "SYSTEM_DEBUG";

struct atm_config {
    LM393& coin_counter_in;
    LM393& coin_counter_out;
    Servo& servo_coin;
};

class ATM {

    private:

    LM393& coin_counter_in;
    LM393& coin_counter_out;
    Servo& servo_coin;

    std::string user_id = "";
    uint8_t _count = 0;
    bool _last_read = false;
    bool _current_read = false;
    int64_t _servo_timer = 0;
    bool _servo_open = false;

    enum States {
        WAITING,
        DEPOSIT,
        WITHDRAW,
    };

    States _current_state;
    int64_t _state_timer;

    public:

    ~ATM() = default;

    ATM(const atm_config& c)
    : /*servo_in(c.servo_in),*/
      coin_counter_in(c.coin_counter_in), coin_counter_out(c.coin_counter_out),
      servo_coin(c.servo_coin), _current_state(WAITING) {

        //servo_in.move(0);
        servo_coin.move(0);
        _state_timer = esp_timer_get_time() / 1000;
    }

    void begin(int core_id) {
        servo_coin.init();
        coin_counter_in.init();
        coin_counter_out.init();
        xTaskCreatePinnedToCore(
            ATM::task_handler,
            "atm_task",
            4096,
            this,
            5,
            NULL,
            core_id
        );

        ESP_LOGD(TAG_D, "Task initialized on core %d.", core_id);
        ESP_LOGD(TAG_D, "Running states machine.");
    }

    void do_deposit(uint8_t num){
        coin_num = num;
        deposit = true;
        withdraw = false;
    }

    void do_withdraw(uint8_t num){
        coin_num = num;
        deposit = false;
        withdraw = true;
    }

    void do_default(){
        coin_num = 0;
        deposit = false;
        withdraw = false;
    }

    std::atomic<bool> withdraw = false;
    std::atomic<bool> deposit = false;
    std::atomic<uint8_t> coin_num = 0;

    private:

    static void task_handler(void* pvParameters) {
        ATM* instance = static_cast<ATM*>(pvParameters);

            while(true) {
                instance->run_machine();
                vTaskDelay(pdMS_TO_TICKS(20));
            }
    }

    void run_machine() {
        switch(_current_state){
            case WAITING:
                if (withdraw) {
                    _current_state = WITHDRAW;
                    _state_timer = esp_timer_get_time() / 1000;
                    _servo_timer = esp_timer_get_time() / 1000;
                    _servo_open = false;
                    _last_read = coin_counter_out.read();
                    _count = 0;
                } else if (deposit) {
                    _current_state = DEPOSIT;
                    //servo_in.move(90);
                    _state_timer = esp_timer_get_time() / 1000;
                    _last_read = coin_counter_in.read();
                    _count = 0;
                }

            break;

            case DEPOSIT:
                if(!coin_counter_in.read()){
                    if (_last_read) {
                        _count++;
                        _last_read = true;
                    }
                } else {
                    _last_read = false;
                }

                if(_count == coin_num || ((esp_timer_get_time() / 1000) - _state_timer) >= 20000){
                    ESP_LOGI(TAG_I, "Deposit complete");
                    ESP_LOGI(TAG_I, "Coin count: %d", _count);
                    printf("DONE DEPOSIT %d\n", (int)_count);
                    coin_num = 0;
                    _count = 0;
                    //servo_in.move(0);
                    _current_state = WAITING;
                    do_default();
                    _state_timer = esp_timer_get_time() / 1000;
                }
            break;

            case WITHDRAW: {
                int64_t current_time = esp_timer_get_time() / 1000;
                if (current_time - _servo_timer >= 1000) {
                    if (!_servo_open) {
                        servo_coin.move(60);
                        _servo_open = true;
                    } else {
                        servo_coin.move(0);
                        _servo_open = false;
                    }
                    _servo_timer = current_time;
                }

                _current_read = coin_counter_out.read();

                if(!coin_counter_out.read()){
                    if (_last_read) {
                        _count++;
                        _last_read = true;
                    }
                } else {
                    _last_read = false;
                }

                if (_count == coin_num || (current_time - _state_timer) >= 20000) {
                    ESP_LOGI(TAG_I, "Withdraw complete");
                    printf("DONE WITHDRAW %d\n", (int)_count);

                    coin_num = 0;
                    _count = 0;
                    servo_coin.move(0);
                    _servo_open = false;

                    _current_state = WAITING;
                    do_default();
                    _state_timer = esp_timer_get_time() / 1000;
                }

            }
            break;
        }
    }

};

#endif
