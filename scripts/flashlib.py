from flipper.assets.coprobin import CoproBinary
from flipper.cube import CubeProgrammer
from typing import Optional
import datetime
import logging


class Flasher:
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.timestamp = int(datetime.datetime.now().timestamp())

    def _getCubeParams(self, port="swd", serial=None):
        return {
            "port": port,
            "serial": serial,
        }

    # Wipe
    def wipe(self, port="swd", serial=None):
        self.logger.info("Wiping flash")
        cp = CubeProgrammer(self._getCubeParams(port, serial))
        self.logger.info("Setting RDP to 0xBB")
        cp.setOptionBytes({"RDP": ("0xBB", "rw")})
        self.logger.info("Verifying RDP")
        r = cp.checkOptionBytes({"RDP": ("0xBB", "rw")})
        assert r is True
        self.logger.info(f"Result: {r}")
        self.logger.info("Setting RDP to 0xAA")
        cp.setOptionBytes({"RDP": ("0xAA", "rw")})
        self.logger.info("Verifying RDP")
        r = cp.checkOptionBytes({"RDP": ("0xAA", "rw")})
        assert r is True
        self.logger.info(f"Result: {r}")
        self.logger.info("Complete")
        return 0

    # Core 1 boot
    def core1bootloader(self, bootloader, address, port="swd", serial=None):
        self.logger.info("Flashing bootloader")
        cp = CubeProgrammer(self._getCubeParams(port, serial))
        cp.flashBin(address, bootloader)
        self.logger.info("Complete")
        cp.resetTarget()
        return 0

    # Core 1 firmware
    def core1firmware(self, firmware, address, port="swd", serial=None):
        self.logger.info("Flashing firmware")
        cp = CubeProgrammer(self._getCubeParams(port, serial))
        cp.flashBin(address, firmware)
        self.logger.info("Complete")
        cp.resetTarget()
        return 0

    # # Core 1 all
    # def core1(self, bootloader, firmware, port="swd", serial=None):
    #     self.logger.info("Flashing bootloader")
    #     cp = CubeProgrammer(self._getCubeParams(port, serial))
    #     cp.flashBin("0x08000000", bootloader)
    #     self.logger.info("Flashing firmware")
    #     cp.flashBin("0x08008000", firmware)
    #     cp.resetTarget()
    #     self.logger.info("Complete")
    #     return 0

    # Core 2 fus
    def core2fus(self, fus_address, fus, port="swd", serial=None):
        self.logger.info("Flashing Firmware Update Service")
        cp = CubeProgrammer(self._getCubeParams(port, serial))
        cp.flashCore2(fus_address, fus)
        self.logger.info("Complete")
        return 0

    # Core 2 radio stack
    def core2radio(self, radio, radio_address=0, port="swd", serial=None):
        stack_info = CoproBinary(radio)
        if not stack_info.is_stack():
            self.logger.error("Not a Radio Stack")
            return 1
        self.logger.info(f"Will flash {stack_info.img_sig.get_version()}")
        if not radio_address:
            radio_address = stack_info.get_flash_load_addr()
            self.logger.warning(
                f"Radio address not provided, guessed as 0x{radio_address:X}"
            )
        if radio_address > 0x080E0000:
            self.logger.error("I KNOW WHAT YOU DID LAST SUMMER")
            return 1
        cp = CubeProgrammer(self._getCubeParams(port, serial))
        self.logger.info("Removing Current Radio Stack")
        cp.deleteCore2RadioStack()
        self.logger.info("Flashing Radio Stack")
        cp.flashCore2(radio_address, radio)
        self.logger.info("Complete")
        return 0
