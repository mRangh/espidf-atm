'''
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
'''

import serial

class UartClient:
    def __init__(self, port='/dev/ttyUSB0', baudrate=115200):
        self.port = port
        self.baudrate = baudrate
        self.esp32 = None

    def connect(self):
        try:
            print(f"[PYTHON]: Connecting on {self.port}...")
            self.esp32 = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS,
                timeout=0.1
            )
            try:
                self.esp32.dtr = False
                self.esp32.rts = False
            except OSError:
                print("[PYTHON_INFO]: Virtual port detected, ignoring DTR/RTS.")

            print("[PYTHON]: Uart client connected")
            return True
        except Exception as e:
            print(f"[PYTHON_ERR]: Uart connection failed: {e}")
            return False

    def send_command(self, cmd_str):
        if self.esp32 and self.esp32.is_open:
            comando = f"{cmd_str}\n"
            self.esp32.write(comando.encode('utf-8'))
            print(f"[UART_SEND]: {comando.strip()}")

    def read_line(self):
        if self.esp32 and self.esp32.is_open and self.esp32.in_waiting > 0:
            line_bytes = self.esp32.readline()
            if line_bytes:
                line_decode = line_bytes.decode('utf-8', errors='ignore').strip()
                return line_decode
        return None

    def close(self):
        if self.esp32 and self.esp32.is_open:
            self.esp32.close()
            print("[PYTHON]: Uart closed.")
