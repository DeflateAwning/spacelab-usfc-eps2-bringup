from machine import I2C, Pin
import time

# SpaceLab EPS 2.0 constants
SL_EPS2_I2C_ADDR = 0x36  # 7-bit I2C slave address
SL_EPS2_DEVICE_ID = 0xEEE2  # Expected device ID

# Registers.
# Source: https://github.com/spacelab-ufsc/obdh2/blob/master/firmware/drivers/sl_eps2/sl_eps2.h
SL_EPS2_REG_TIME_COUNTER_MS = 0
SL_EPS2_REG_UC_TEMPERATURE_K = 1
SL_EPS2_REG_LAST_RESET_CAUSE = 3  #  /**< Last reset cause. */
SL_EPS2_REG_RESET_COUNTER = 4  #   /**< Reset counter. */
SL_EPS2_REG_MAIN_POWER_BUS_VOLT_MV = 18  #   /**< Main power bus voltage in mV. */
SL_EPS2_REG_DEVICE_ID = 48  # Device ID (0xEEE2).


SL_EPS2_CRC8_INITIAL_VALUE = 0x00
SL_EPS2_CRC8_POLYNOMIAL = 0x07


def crc8(data: bytes) -> int:
    """Compute CRC8-CCITT over the given data (bytes)."""
    # assert len(data) == 5, f"Data must be exactly 5 bytes, was {len(data)}" # TODO: Maybe re-enable this?

    crc = SL_EPS2_CRC8_INITIAL_VALUE

    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x80:
                crc = ((crc << 1) ^ SL_EPS2_CRC8_POLYNOMIAL) & 0xFF
            else:
                crc = (crc << 1) & 0xFF

    return crc


# --- EPS2 Driver Functions ---
class EPS2:
    def __init__(self, i2c: I2C, addr=SL_EPS2_I2C_ADDR):
        self.i2c = i2c
        self.addr = addr

    def read_reg(self, reg: int) -> int:
        """Read 32-bit register with CRC check"""
        # Write register + CRC
        outbuf = bytes([reg, crc8(bytes([reg]))])

        # TODO: Check on this part - outbuf should be 5 or 6 bytes long (address, 4 reg bytes, crc8)
        # buf[0] = adr; # Not used directly.
        # buf[1] = (val >> 24) & 0xFFU;
        # buf[2] = (val >> 16) & 0xFFU;
        # buf[3] = (val >> 8)  & 0xFFU;
        # buf[4] = (val >> 0)  & 0xFFU;
        # reg_buf = [
        #     (reg >> 24) & 0xFF,
        #     (reg >> 16) & 0xFF,
        #     (reg >> 8) & 0xFF,
        #     (reg >> 0) & 0xFF,
        # ]
        # outbuf = bytes(reg_buf) + bytes(
        #     [
        #         crc8(
        #             bytes(
        #                 [
        #                     self.addr,
        #                     (reg >> 24) & 0xFF,
        #                     (reg >> 16) & 0xFF,
        #                     (reg >> 8) & 0xFF,
        #                     (reg >> 0) & 0xFF,
        #                 ]
        #             )
        #         )
        #     ]
        # )
        print("Writing:", [hex(b) for b in outbuf])

        self.i2c.writeto(self.addr, outbuf)

        time.sleep_ms(50)  # device delay

        # Read back (reg + 4 data + crc) = 6 bytes
        buf = self.i2c.readfrom(self.addr, 6)

        print("Raw data (from EPS):", [hex(b) for b in buf])

        # Check CRC on first 5 bytes
        if crc8(buf[:5]) != buf[5]:
            # raise ValueError("CRC mismatch")
            print("CRC mismatch on read! Continuing.")

        # Convert 4-byte big-endian payload
        # Note: buf[0] is the register echoed back.
        val = (buf[1] << 24) | (buf[2] << 16) | (buf[3] << 8) | buf[4]
        return val

    def get_reset_cause(self) -> int:
        return self.read_reg(SL_EPS2_REG_LAST_RESET_CAUSE)

    def get_reset_count(self) -> int:
        return self.read_reg(SL_EPS2_REG_RESET_COUNTER)

    def get_device_id(self) -> int:
        return self.read_reg(SL_EPS2_REG_DEVICE_ID)

    def get_temperature_k(self) -> float:
        val = self.read_reg(SL_EPS2_REG_UC_TEMPERATURE_K)
        return float(val)  # in Kelvin (per datasheet)

    def get_temperature_c(self) -> float:
        return self.get_temperature_k() - 273.15


def i2c_scan(i2c):
    print("Scanning I2C bus...")
    devices = i2c.scan()
    if not devices:
        print("No I2C devices found")
    else:
        print("Found {} device(s):".format(len(devices)))
        for dev in devices:
            print(" - Address: 0x{:02X}".format(dev))


# --- Example Usage ---
# Adjust I2C pins for your board!
i2c = I2C(
    0,
    scl=Pin(5, Pin.OPEN_DRAIN, Pin.PULL_UP),
    sda=Pin(4, Pin.OPEN_DRAIN, Pin.PULL_UP),
    freq=100000,
)


def main():
    eps = EPS2(i2c)

    try:
        i2c_scan(i2c)
    except Exception as e:
        print("I2C scan error:", e)

    print()
    print("START: Fetch Device ID")
    device_id = eps.get_device_id()
    print(f"Device ID: 0x{device_id:02X}")
    if device_id != SL_EPS2_DEVICE_ID:
        print("⚠ Unexpected device ID! Continuing.")

    print()
    print("START: Fetch Temperature")
    temp_k = eps.get_temperature_k()
    # temp_c = eps.get_temperature_c()
    temp_c = temp_k - 273.15

    print("Temperature: {:.2f} K / {:.2f} °C".format(temp_k, temp_c))

    print()
    print("START: Fetch Reset Cause/Reason")
    reset_cause = eps.get_reset_cause()
    print(f"Last Reset Cause: 0x{reset_cause:02X}")

    print()
    print("START: Fetch Reset Count")
    reset_count = eps.get_reset_count()
    print(f"Reset Count: {reset_count}")

    print()
    print("START: Fetch Main Power Bus Voltage")
    main_power_bus_voltage = eps.read_reg(SL_EPS2_REG_MAIN_POWER_BUS_VOLT_MV)
    print(f"Main Power Bus Voltage: {main_power_bus_voltage} mV")


main()
