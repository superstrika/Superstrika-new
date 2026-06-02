import time
from smbus2 import SMBus

class VCNL4040:
    # --- Constants ---
    ALS_80MS = 0x0
    ALS_160MS = 0x1
    ALS_320MS = 0x2
    ALS_640MS = 0x3

    # Proximity integration times
    PS_1T = 0x0
    PS_1_5T = 0x1
    PS_2T = 0x2
    PS_2_5T = 0x3
    PS_3T = 0x4
    PS_3_5T = 0x5
    PS_4T = 0x6
    PS_8T = 0x7

    # Interrupt Flags
    ALS_IF_L = 13
    ALS_IF_H = 12
    PS_IF_CLOSE = 9
    PS_IF_AWAY = 8

    # LED Current levels
    LED_50MA = 0x0
    LED_75MA = 0x1
    LED_100MA = 0x2
    LED_120MA = 0x4
    LED_140MA = 0x4
    LED_160MA = 0x5
    LED_180MA = 0x6
    LED_200MA = 0x7

    def __init__(self, bus_number=1, address=0x60):
        self.address = address
        self.bus = SMBus(bus_number)

        # Verify Device ID (Register 0x0C should return 0x0186)
        if self._read_reg(0x0C) != 0x0186:
            raise RuntimeError("VCNL4040 not found at address 0x60")

        self.cached_interrupt_state = {
            self.ALS_IF_L: False, self.ALS_IF_H: False,
            self.PS_IF_CLOSE: False, self.PS_IF_AWAY: False,
        }

        # Initialize: Power on Proximity and Ambient Light
        self.proximity_shutdown = False
        self.light_shutdown = False

    # --- Low Level SMBus Helpers ---
    def _read_reg(self, reg):
        """Reads a 16-bit word from the register."""
        return self.bus.read_word_data(self.address, reg)

    def _write_reg(self, reg, value):
        """Writes a 16-bit word to the register."""
        self.bus.write_word_data(self.address, reg, value & 0xFFFF)

    def _modify_bits(self, reg, value, mask, shift):
        """Read-Modify-Write to handle specific bits within a 16-bit register."""
        current = self._read_reg(reg)
        new_val = (current & ~mask) | ((value << shift) & mask)
        self._write_reg(reg, new_val)

    # --- Data Properties ---
    @property
    def proximity(self):
        """Returns the proximity value (12 or 16-bit depending on config)."""
        return self._read_reg(0x08)

    @property
    def light(self):
        """Returns raw ambient light data."""
        return self._read_reg(0x09)

    @property
    def lux(self):
        """Returns ambient light in lux based on integration time."""
        return self.light * (0.1 / (1 << self.light_integration_time))

    # --- Configuration ---
    @property
    def proximity_shutdown(self):
        return bool(self._read_reg(0x03) & 0x0001)

    @proximity_shutdown.setter
    def proximity_shutdown(self, val):
        self._modify_bits(0x03, int(val), 0x0001, 0)

    @property
    def light_shutdown(self):
        return bool(self._read_reg(0x00) & 0x0001)

    @light_shutdown.setter
    def light_shutdown(self, val):
        self._modify_bits(0x00, int(val), 0x0001, 0)

    @property
    def light_integration_time(self):
        return (self._read_reg(0x00) >> 6) & 0x03

    @light_integration_time.setter
    def light_integration_time(self, new_it):
        # Calculate delay needed for sensor to settle (from original library)
        old_it = self.light_integration_time
        it_delay = ((8 << old_it) * 10 + (8 << new_it) * 10 + 1) * 0.001
        self._modify_bits(0x00, new_it, 0x00C0, 6)
        time.sleep(it_delay)

    @property
    def led_current(self):
        """Returns the current LED current setting (0-7)."""
        return (self._read_reg(0x03) >> 8) & 0x07

    @led_current.setter
    def led_current(self, level):
        """Sets the LED current (0=50mA, 7=200mA). Use constants like LED_200MA."""
        self._modify_bits(0x03, level, 0x0700, 8)

    @property
    def proximity_integration_time(self):
        """Returns the proximity integration time setting (0-7)."""
        return (self._read_reg(0x03) >> 1) & 0x07

    @proximity_integration_time.setter
    def proximity_integration_time(self, new_it):
        """Sets the proximity integration time (1T to 8T). Use constants like PS_8T."""
        self._modify_bits(0x03, new_it, 0x000E, 1)

    @property
    def proximity_high_definition(self):
        """Returns True if 16-bit mode is enabled, False if 8-bit."""
        return bool((self._read_reg(0x03) >> 3) & 0x0001)

    @proximity_high_definition.setter
    def proximity_high_definition(self, val):
        """Set to True for 16-bit (0-65535) or False for 8-bit (0-255)."""
        self._modify_bits(0x03, int(val), 0x0008, 3)

    # --- Interrupt Handling ---
    def _update_interrupt_state(self):
        reg_val = self._read_reg(0x0B)
        for bit in [self.PS_IF_AWAY, self.PS_IF_CLOSE, self.ALS_IF_H, self.ALS_IF_L]:
            if reg_val & (1 << bit):
                self.cached_interrupt_state[bit] = True

    def _get_and_clear_interrupt(self, bit_offset):
        self._update_interrupt_state()
        state = self.cached_interrupt_state[bit_offset]
        self.cached_interrupt_state[bit_offset] = False
        return state

    @property
    def proximity_high_interrupt(self):
        return self._get_and_clear_interrupt(self.PS_IF_CLOSE)

if __name__ == "__main__":
    sensor = VCNL4040()
    sensor.led_current = VCNL4040.LED_100MA
    sensor.proximity_high_definition = True
    sensor.proximity_integration_time = VCNL4040.PS_8T
    print("VCNL4040 Ready (smbus2)")

    import robot.consts.data as data

    def getBallStatus(vcnl) -> data.BallStatus:
        vcnl_prox = vcnl.proximity

        cam_found = False
        if vcnl_prox < data.VCNL_PROX_NOT_DETECTED and not cam_found:
            return data.BallStatus.NOT_FOUND
        
        if cam_found and vcnl_prox < data.VCNL_PROX_NOT_DETECTED:
            return data.BallStatus.CAM_DETECTED
        
        if not cam_found and data.VCNL_PROX_IN_KICKER > vcnl_prox > data.VCNL_PROX_NOT_DETECTED:
            return data.BallStatus.VCNL_CLOSE
        
        if not cam_found and data.VCNL_PROX_IN_KICKER < vcnl_prox:
            return data.BallStatus.VCNL_IN_KICKER
        
        return data.BallStatus.CAM_DETECTED_AND_VCNL_CLOSE
    
    try:
        while True:
            print(f"Proximity: {sensor.proximity:5} | Status: {getBallStatus(sensor)}")
            time.sleep(0.2)
    except KeyboardInterrupt:
        print("\nExiting.")