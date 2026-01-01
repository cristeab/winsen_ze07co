#!/usr/bin/env python3
# Winsen ZE07 Carbon Monoxide Sensor Interface

import serial
import time
from datetime import datetime
import logging


class CarbonMonoxideDetector:
    BAUD_RATE = 9600
    PACKET_SIZE = 9
    START_BYTE = b'\xff'
    def __init__(self, port='/dev/ttyACM0', logger=None, level=logging.INFO):
        if logger is None:
            logging.basicConfig(level=level)
            self.logger = logging.getLogger(self.__class__.__name__)
        else:
            self.logger = logger

        try:
            self._ser = serial.Serial(port, self.BAUD_RATE, timeout=1)
            self.logger.info(f"Connected to {port} at {self.BAUD_RATE} bauds.")
        except serial.SerialException as e:
            self.logger.error(f"Serial Error: {e}")
            raise

    @staticmethod
    def _calculate_checksum(data):
        payload = data[1:8]
        checksum = sum(payload) & 0xFF
        checksum = ((~checksum) & 0xFF) + 1
        return checksum & 0xFF

    def set_initiative_upload_mode(self):
        if not self._ser or not self._ser.is_open:
            self.logger.error("Serial port not open")
            return False

        command = bytearray([0xFF, 0x01, 0x78, 0x40, 0x00, 0x00, 0x00, 0x00])
        checksum = CarbonMonoxideDetector._calculate_checksum(command)
        command.append(checksum)

        self.logger.debug(f"Setting initiative upload mode {command.hex()}...")
        self._ser.write(command)
        time.sleep(0.1)

    def get_initiative_co_ppm(self):
        if not self._ser or not self._ser.is_open:
            self.logger.error("Serial port not open")
            return None

        # Look for the start byte 0xFF
        byte = self._ser.read(1)
        if not byte:
            return None
            
        if byte == self.START_BYTE:
            # Read the remaining 8 bytes of the packet
            data = self._ser.read(self.PACKET_SIZE - 1)
            
            if len(data) == (self.PACKET_SIZE - 1):
                full_packet = self.START_BYTE + data
                
                # Verify Checksum
                received_checksum = full_packet[self.PACKET_SIZE - 1]
                calculated_checksum = CarbonMonoxideDetector._calculate_checksum(full_packet)
                
                if received_checksum == calculated_checksum:
                    high_byte = full_packet[4]
                    low_byte = full_packet[5]
                    ppm = ((high_byte * 256) + low_byte) * 0.1
                    
                    return ppm
                else:
                    self.logger.warning("Checksum mismatch! Data corrupted.")
                    return None
        return None

    def set_qa_mode(self):
        if not self._ser or not self._ser.is_open:
            self.logger.error("Serial port not open")
            return False

        command = bytearray([0xFF, 0x01, 0x78, 0x41, 0x00, 0x00, 0x00, 0x00])
        checksum = CarbonMonoxideDetector._calculate_checksum(command)
        command.append(checksum)

        self.logger.debug(f"Setting question and answer mode {command.hex()}...")
        self._ser.write(command)
        time.sleep(0.1)

    def get_qa_co_ppm(self):
        if not self._ser or not self._ser.is_open:
            self.logger.error("Serial port not open")
            return None

        command = bytearray([0xFF, 0x01, 0x86, 0x00, 0x00, 0x00, 0x00, 0x00])
        checksum = CarbonMonoxideDetector._calculate_checksum(command)
        command.append(checksum)

        self.logger.debug(f"Requesting CO data {command.hex()}...")
        self._ser.write(command)
        time.sleep(0.1)

        response = self._ser.read(self.PACKET_SIZE)
        if len(response) == self.PACKET_SIZE and response[0] == 0xFF and response[1] == 0x86:
            self.logger.debug(f"Received response {response.hex()}")

            received_checksum = response[self.PACKET_SIZE - 1]
            calculated_checksum = CarbonMonoxideDetector._calculate_checksum(response)

            if received_checksum == calculated_checksum:
                high_byte = response[2]
                low_byte = response[3]
                ppm = ((high_byte * 256) + low_byte) * 0.1

                return ppm
            else:
                self.logger.warning("Checksum mismatch! Data corrupted.")
                return None
        else:
            self.logger.warning("Invalid response length or header.")
        return None

# Example usage
if __name__ == "__main__":
    co_detector = CarbonMonoxideDetector(level=logging.DEBUG)
    #co_detector.set_initiative_upload_mode()
    co_detector.set_qa_mode()
    while True:
        #co_ppm = co_detector.get_initiative_co_ppm()
        co_ppm = co_detector.get_qa_co_ppm()
        if co_ppm is not None:
            co_detector.logger.info(f"{datetime.now()}: CO Concentration: {co_ppm} PPM")
        time.sleep(3)
