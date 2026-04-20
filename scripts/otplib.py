from typing import Optional, Tuple
import datetime
import logging
import struct
import os
import re

from flipper.utils.programmer_openocd import OpenOCDProgrammer, OpenOCDProgrammerResult

OTP_MAGIC = 0xBABE
OTP_VERSION = 0x02
OTP_RESERVED = 0x00

OTP_COLORS = {
    "unknown": 0x00,
    "black": 0x01,
    "white": 0x02,
    "transparent": 0x03,
}

OTP_REGIONS = {
    "unknown": 0x00,
    "eu_ru": 0x01,
    "us_ca_au": 0x02,
    "jp": 0x03,
    "world": 0x04,
}

OTP_DISPLAYS = {
    "unknown": 0x00,
    "erc": 0x01,
    "mgg": 0x02,
}


class OTP:
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.timestamp = int(datetime.datetime.now().timestamp())

    def _validate_first_args(
        self, version: int, firmware: int, body: int, connect: int, display: str
    ) -> int:
        if display not in OTP_DISPLAYS:
            raise ValueError(
                f"Invalid display '{display}'. Valid options: {list(OTP_DISPLAYS.keys())}"
            )
        return OTP_DISPLAYS[display]

    def _validate_second_args(
        self, color: str, region: str, name: str
    ) -> tuple[int, int, bytes]:
        if color not in OTP_COLORS:
            raise ValueError(
                f"Invalid color '{color}'. Valid options: {list(OTP_COLORS.keys())}"
            )
        if region not in OTP_REGIONS:
            raise ValueError(
                f"Invalid region '{region}'. Valid options: {list(OTP_REGIONS.keys())}"
            )
        if len(name) > 8:
            raise ValueError("Name is too long. Maximum 8 characters allowed.")
        if not re.match(r"^[a-zA-Z0-9.]+$", name):
            raise ValueError(
                "Name contains invalid characters. Only a-z, A-Z, 0-9 and '.' allowed."
            )

        return (
            OTP_COLORS[color],
            OTP_REGIONS[region],
            name.encode("ascii").ljust(8, b"\x00"),
        )

    def _pack_first(
        self, version: int, firmware: int, body: int, connect: int, display: str
    ) -> bytes:
        display_val = self._validate_first_args(
            version, firmware, body, connect, display
        )

        return struct.pack(
            "<HBBLBBBBBBH",
            OTP_MAGIC,
            OTP_VERSION,
            OTP_RESERVED,
            self.timestamp,
            version,
            firmware,
            body,
            connect,
            display_val,
            OTP_RESERVED,
            OTP_RESERVED,
        )

    def _pack_second(self, color: str, region: str, name: str) -> bytes:
        color_val, region_val, name_bytes = self._validate_second_args(
            color, region, name
        )

        return struct.pack(
            "<BBHL8s",
            color_val,
            region_val,
            OTP_RESERVED,
            OTP_RESERVED,
            name_bytes,
        )

    def generate(
        self,
        version: int,
        firmware: int,
        body: int,
        connect: int,
        display: str,
        color: str,
        region: str,
        name: str,
        output_dir: str = ".",
        base_name: str = "",
    ) -> Tuple[str, str]:

        self.logger.info("Generating OTP binary files...")

        first_data = self._pack_first(version, firmware, body, connect, display)
        second_data = self._pack_second(color, region, name)

        os.makedirs(output_dir, exist_ok=True)

        if base_name != "":
            first_path = os.path.join(output_dir, f"{base_name}_first.bin")
            second_path = os.path.join(output_dir, f"{base_name}_second.bin")
        else:
            first_path = os.path.join(output_dir, f"first.bin")
            second_path = os.path.join(output_dir, f"second.bin")

        with open(first_path, "wb") as f:
            f.write(first_data)
        with open(second_path, "wb") as f:
            f.write(second_data)

        self.logger.info(f"OTP files generated:")
        self.logger.info(f"- {first_path}")
        self.logger.info(f"- {second_path}")
        return first_path, second_path

    def flash_all(
        self,
        first_file: str,
        second_file: str,
        first_address: int,  # 0x1FFF7000
        second_address: int,  # 0x1FFF7010
        interface: str = "interface/stlink.cfg",
        port_base: int = 3333,
        serial: Optional[str] = None,
    ) -> None:

        try:
            with open(first_file, "rb") as f:
                first_data = f.read()
            with open(second_file, "rb") as f:
                second_data = f.read()

            self._flash_data(first_data, first_address, interface, port_base, serial)
            self._flash_data(second_data, second_address, interface, port_base, serial)

        except FileNotFoundError as e:
            raise Exception(f"OTP file not found: {e.filename}") from e

    def flash_first(
        self,
        first_file: str,
        address: int,  # 0x1FFF7000
        interface: str = "interface/stlink.cfg",
        port_base: int = 3333,
        serial: Optional[str] = None,
    ) -> None:
        """Flash only the first OTP block from file."""
        self.logger.info("Flashing first OTP block")
        with open(first_file, "rb") as f:
            data = f.read()
        self._flash_data(data, address, interface, port_base, serial)

    def flash_second(
        self,
        second_file: str,
        address: int,  # 0x1FFF7010
        interface: str = "interface/stlink.cfg",
        port_base: int = 3333,
        serial: Optional[str] = None,
    ) -> None:
        self.logger.info("Flashing second OTP block")
        with open(second_file, "rb") as f:
            data = f.read()
        self._flash_data(data, address, interface, port_base, serial)

    def _flash_data(
        self,
        data: bytes,
        address: int,
        interface: str,
        port_base: int,
        serial: Optional[str],
    ) -> None:
        temp_file = f"otp_flash_temp_{self.timestamp}.bin"

        try:
            with open(temp_file, "wb") as f:
                f.write(data)

            programmer = OpenOCDProgrammer(interface, port_base, serial)
            result = programmer.otp_write(address, temp_file)

            if result != OpenOCDProgrammerResult.Success:
                raise Exception(f"Failed to flash OTP: {result}")

            self.logger.info(f"OTP flashed successfully at address 0x{address:X}")

        finally:
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except Exception:
                    pass
