#!/usr/bin/env python3
# Winsen ZE07 Carbon Monoxide Sensor Interface

import serial
import time
from datetime import datetime
import logging


class CarbonMonoxideDetector:
    def __init__(self, logger=None, level=logging.INFO, port='/dev/ttyACM0', baud=9600):
        if logger is None:
            logging.basicConfig(level=level)
            self.logger = logging.getLogger(self.__class__.__name__)
        else:
            self.logger = logger

        try:
            self._ser = serial.Serial(port, baud, timeout=1)
            self.logger.info(f"Connected to {port} at {baud} baud.")
        except serial.SerialException as e:
            self.logger.error(f"Serial Error: {e}")
            raise

    @staticmethod
    def _calculate_checksum(data):
        """
        Checksum = (NOT (Byte1 + Byte2 + Byte3 + Byte4 + Byte5 + Byte6 + Byte7)) + 1
        """
        payload = data[1:8]
        checksum = sum(payload) & 0xFF
        checksum = ((~checksum) & 0xFF) + 1
        return checksum & 0xFF

    def get_co_ppm(self):
        if not self._ser or not self._ser.is_open:
            self.logger.error("Serial port not open")
            return None

        # Look for the start byte 0xFF
        byte = self._ser.read(1)
        if not byte:
            return None
            
        if byte == b'\xff':
            # Read the remaining 8 bytes of the packet
            data = self._ser.read(8)
            
            if len(data) == 8:
                full_packet = b'\xff' + data
                
                # Verify Checksum
                received_checksum = full_packet[8]
                calculated_checksum = CarbonMonoxideDetector._calculate_checksum(full_packet)
                
                if received_checksum == calculated_checksum:
                    # Concentration = MSB * 256 + LSB
                    high_byte = full_packet[4]
                    low_byte = full_packet[5]
                    ppm = ((high_byte * 256) + low_byte) * 0.1
                    
                    return ppm
                else:
                    self.logger.error("Checksum mismatch! Data corrupted.")
                    return None
        return None

    def read_loop(self):
        self.connect()
        try:
            while True:
                ppm = self.read_once()
                if ppm is not None:
                    print(f"{datetime.now()}: CO Concentration: {ppm} PPM")
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\nStopping...")
        finally:
            if self.ser and self.ser.is_open:
                self.ser.close()

if __name__ == "__main__":
    co_detector = CarbonMonoxideDetector()
    while True:
        co_ppm = co_detector.get_co_ppm()
        if co_ppm is not None:
            co_detector.logger.info(f"{datetime.now()}: CO Concentration: {co_ppm} PPM")
        time.sleep(0.1)
