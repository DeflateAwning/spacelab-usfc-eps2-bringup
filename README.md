# SpaceLab USFC EPS2 Bringup

Notes and testing code for working with the [USFC SpaceLab EPS2](https://github.com/spacelab-ufsc/eps2) open source EPS

## Contents

* `eps2_i2c_obdh_emulator.py` - MicroPython script to command the EPS and read back properties

## Notes

* Uses the MSP430F6659 microcontroller.

## Guide: Dev Setup and Flashing

1. On Windows, install TI's Code Composer Studio (CCS) v20+.
    * Did not have success with the drivers on Linux, yet.
2. Install Windows drivers for MSP430 [(`MSP430_FET_Drivers  1_0_1_1`)](https://software-dl.ti.com/msp430/msp430_public_sw/mcu/msp430/MSP430_FET_Drivers/latest/index_FDS.html).
3. Install MSPFlasher.
4. Buy the [MSP430 Emulator MSP-FET430UIF USB Debug Interface Programmer](https://www.aliexpress.com/item/1005006750862890.html). The $20 AliExpress version works.
5. Open a Terminal in `C:\ti\MSPFlasher...\`, and run `.\MSPFlasher.exe -n MSP430F6659`. Follow the procedure to update the programmer's firmware. This step cannot be skipped.
6. Connect the EPS to the programmer (GND, two data lines, and voltage).
7. Jump CN1 connector the on the EPS.
8. Observe 2 LEDs on the back turned on.
9. Flash the EPS from CCS.
10. Connect a USB-UART converter at 115200 baud 8N1 to the UART port. Note that this UART port appears to be EPS-output only (i.e., the EPS does not receive through this UART port, as far as I can tell).
11. Observe that the bootup works and that log messages appear on the UART line. Observe that the `SYSTEM_ON` LED blinks at 1 Hz.
12. Connect an RP2040-Zero running MicroPython via the Stack Header.
    * RP2040-Zero Pin 4 = SDA = EPS H2-49
    * RP2040-Zero Pin 5 = SCL = EPS H2-51
    * GND = GND = GND [don't forget]
13. Run the MicroPython script in this repo (`eps2_i2c_obdh_emulator.py`). One method is [explained in DeflateAwning's MicroPython setup guide](https://gist.github.com/DeflateAwning/cfc26095d25390fcd3c619176c7bf23e). Thony is another option.
14. Observe the MicroPython output: I2C scan succeeds, telemetry data is received.
