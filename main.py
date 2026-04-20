import os
import logging
import colorlog
import yaml
import subprocess
from Crypto.Cipher import AES
import random
import sys
from pathlib import Path

root = Path(__file__).parent
sys.path.insert(0, str(root / "scripts"))

from scripts.otplib import OTP
from scripts.flashlib import Flasher

banner = """
         @@@#.  .-@@@@                                  @@*                        @  
     @@@-             .@@@                            @@     .....:::... ...  .:.  @  
.#@@+     ::..:......     @@    #@@@@@@@ @@==+===@@@@@@   ........   :..........:  @  
 .    ..=:.   .... ..:::.   @@=:..      ..              . ..... .:::...:-.-=..==  .@  
   :...-.....:..::....  ...        .:.........-: ........:.. ...-.... ...-......  @   
   .:..-........=:.:=.:.:.::...:  -: ......... ..  ........:..  .:-.....:-....   @    
 ...=.. --.:::-= .....::.......  =: ............ @  ...  .....:: ..:===-.. ..  %@     
 ==:.............. ......  ....  @  ............  @  ..=:  ....:.. ........   @@      
 ............   .:......  =:..  @  .............  %@ ....=.  ..........    -@@        
:-           == ......  :=  .. =  ...............  @  ... ==  .....::.-*@@@@          
 @@@@@@@@@@@ @. .....  =....   @  ................  * ...   @  .......@               
            @  .....  =:.. . .@@ .................  @   ...  @. ..... .@              
           @  .....  =. .:  =@ @ .................  %@. ....  -  ....   @             
         @=  .....  :=  .  +@  @  . .............. :# @:  ...  @  .....  @            
        @=  ...... :*     @*   @. =  ............  =   #@   ..  %  .....  @           
       @.........  *     @. ::  @ .@  ..........   @     @:   . :@  ..... .@          
      @:@ . ....  =-   =@ :     @= @:   .......  -@*      #@:    -@ .....  :@         
     @ @  ......  @  .@*         @. @@    ....  :=@         =@=  .@  .....  #         
    @:@: ....... +  =@             @.@*@:      -@@             %@::@  .....  @        
   @ =@   ...... =:@=     @@@@@@@   =@# *@@==:=@=  @@@@@@@@@@%   .*@= .  ... .@       
   -- @  : ..... @@    @@@@%%%-@@@            +    @@       @@@@    @ . =- .. .@      ███████╗██╗     ██╗██████╗ ██████╗ ███████╗██████╗            
  @ @@  :: ....  %   @@@% @:...@  @               @ %:::--:@  *@@@  @ . ::: .   @     ██╔════╝██║     ██║██╔══██╗██╔══██╗██╔════╝██╔══██╗           
  @. @  *  .... =+ @@@  @:. .:.:@                   @.+ ==.:*@  @@@ =.  :::..  @ @    █████╗  ██║     ██║██████╔╝██████╔╝█████╗  ██████╔╝           
  @- #  @  .... @=@@   @:.:+%+=::@                  @:..::*#=:@  -@@@.  =.: .  @% @   ██╔══╝  ██║     ██║██╔═══╝ ██╔═══╝ ██╔══╝  ██╔══██╗           
  @:@=  @  .... @@@   @:=*=*.-:.:%                  *. :*:  ..@    @@@  @ : .. -@ =   ██║     ███████╗██║██║     ██║     ███████╗██║  ██║           
  -:@  ..* ..   %@:   @ .   #*  :@                   +        @    @@=  @.  ..  @ @@  ╚═╝     ╚══════╝╚═╝╚═╝     ╚═╝     ╚══════╝╚═╝  ╚═╝           
   =@  : @    =@@@    @.      ..*                      .:.:::.%     @: @** . .  @ @@                                                                
    @  . @@.     @+    @.:::.:                                      %=- ** . =  @ @   ███████╗███████╗██████╗  ██████╗                              
    @:  .@ @     @    #                                  .:==####+- +:@  .   *  @@@   ╚══███╔╝██╔════╝██╔══██╗██╔═══██╗                             
     *   @ *@=:  @   :-=*#**+==:                  @      :==++=+*#= %@  @  : @ @        ███╔╝ █████╗  ██████╔╝██║   ██║                             
     @   .@  *@=  @ :*+=====-=:       *%%*#%%#**=           .::.     *@%: . = :@       ███╔╝  ██╔══╝  ██╔══██╗██║   ██║                             
     @    :@:  *@  @  -=-:::                                         @.:    @-@       ███████╗███████╗██║  ██║╚██████╔╝                             
      @=:  .=@@ @=@*@                                               @::.   @@         ╚══════╝╚══════╝╚═╝  ╚═╝ ╚═════╝                              
       --%    -.=@  :                                              @#:. ..@@                                                                        
       @:-@    :::@                                              *@..  .#:            ███████╗ █████╗  ██████╗████████╗ ██████╗ ██████╗ ██╗   ██╗   
         % @:    ::@*                                          *@.-  .=@              ██╔════╝██╔══██╗██╔════╝╚══██╔══╝██╔═══██╗██╔══██╗╚██╗ ██╔╝   
          @==@@    :=@@                                     *@-.:@@:@@                █████╗  ███████║██║        ██║   ██║   ██║██████╔╝ ╚████╔╝    
             @@@@@    .=@@                               @@= #@@@ @                   ██╔══╝  ██╔══██║██║        ██║   ██║   ██║██╔══██╗  ╚██╔╝     
                %@=@@@:::-=@@@*                      @@=:. -@@*                       ██║     ██║  ██║╚██████╗   ██║   ╚██████╔╝██║  ██║   ██║      
                    =@@  @@=-=@====@#  -      .==== @::@=@@@                          ╚═╝     ╚═╝  ╚═╝ ╚═════╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝   ╚═╝      
                                 @@%@@ :-==+==-:::. @                                                                                               
                                      . ::::.:::::  . @                               ███████╗██╗      █████╗ ███████╗██╗  ██╗██╗███╗   ██╗ ██████╗ 
                                   #@@#::    .   -*%@ *                               ██╔════╝██║     ██╔══██╗██╔════╝██║  ██║██║████╗  ██║██╔════╝ 
                   @              @    :.@@@   @:     @@@@%                           █████╗  ██║     ███████║███████╗███████║██║██╔██╗ ██║██║  ███╗
                 @      @@@@@*=@   @        @:*      =@  @@=*@@@+      @              ██╔══╝  ██║     ██╔══██║╚════██║██╔══██║██║██║╚██╗██║██║   ██║
                @         @...:@    @*       @      @     @...@         =             ██║     ███████╗██║  ██║███████║██║  ██║██║██║ ╚████║╚██████╔╝
                          :            %          %       :    @        =             ╚═╝     ╚══════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝ ╚═════╝ 
"""

finish_banner = """
 ██████╗ ██╗  ██╗██╗
██╔═══██╗██║ ██╔╝██║
██║   ██║█████╔╝ ██║
██║   ██║██╔═██╗ ╚═╝
╚██████╔╝██║  ██╗██╗
 ╚═════╝ ╚═╝  ╚═╝╚═╝
"""


class FactoryFlasher:
    def __init__(self):
        self.logger = logging.getLogger()

        sh = colorlog.StreamHandler()
        formatter = colorlog.ColoredFormatter(
            "%(log_color)s%(asctime)s [%(funcName)s]: %(message)s"
        )
        sh.setFormatter(formatter)
        self.logger.addHandler(sh)
        self.logger.setLevel(logging.INFO)

        self.config = yaml.safe_load(open("config.yaml"))

        self.OTP = OTP(logger=self.logger)
        self.Flasher = Flasher(logger=self.logger)

        self.OTP_first_file, self.OTP_second_file = None, None

        self.encrypted_key_iv = [
            [0x38, 0xB3, 0xEC, 0x3B, 0x3C, 0x5D, 0x34, 0x29, 0x8C, 0x38, 0x2E, 0xA8],
            [0xDF, 0x26, 0x9C, 0x42, 0xEE, 0x03, 0xEF, 0x0E, 0x49, 0x71, 0x1C, 0xDA],
            [0xD8, 0x96, 0x63, 0xF3, 0x27, 0x3B, 0xBF, 0xDF, 0x88, 0x64, 0x5B, 0xA6],
            [0x36, 0xFE, 0x95, 0x29, 0xEC, 0x19, 0xA2, 0x84, 0xDC, 0xAD, 0xC8, 0xDA],
            [0x19, 0x56, 0xA3, 0x53, 0xF2, 0xD5, 0x12, 0x01, 0x36, 0x1B, 0x09, 0x30],
            [0x2E, 0xAA, 0x02, 0x90, 0xC0, 0xDB, 0x42, 0x8B, 0x50, 0x14, 0x5D, 0x3B],
            [0xAF, 0x35, 0xCA, 0x82, 0x19, 0x9C, 0xC9, 0x99, 0x49, 0x4C, 0xA4, 0x4A],
            [0xD9, 0x81, 0xFF, 0xA0, 0xC1, 0x5F, 0x90, 0x2A, 0x65, 0x4B, 0xEF, 0x78],
            [0x02, 0xDF, 0xCA, 0xCD, 0xEC, 0xA0, 0xD6, 0xF9, 0xAE, 0xD8, 0x7E, 0x19],
            [0xD4, 0xFD, 0x39, 0xC6, 0x74, 0x0E, 0xC9, 0xD3, 0x09, 0x18, 0xAB, 0x76],
        ]

    def _to_int(self, value):
        if isinstance(value, int):
            return value
        elif isinstance(value, str):
            if value.lower().startswith("0x"):
                return int(value, 16)  # hex string
            else:
                return int(value)  # decimal string
        else:
            raise TypeError(f"Cannot convert {type(value)} to int")

    def aes128gcm_encrypt(self, key: bytes, iv: bytes, plaintext: bytes):
        cipher = AES.new(key, AES.MODE_GCM, iv)
        cipher.block_size = 128
        ciphertext = cipher.encrypt(plaintext)
        self.logger.debug(cipher.digest().hex().upper())
        return ciphertext

    def generate_OTP(self):
        self.logger.info("Trying to generate OTP")

        # Get the OTP config
        version = self.config["OTP"]["version"]
        firmware = self.config["OTP"]["firmware"]
        body = self.config["OTP"]["body"]
        connect = self.config["OTP"]["connect"]
        display = self.config["OTP"]["display"]
        color = self.config["OTP"]["color"]
        region = self.config["OTP"]["region"]
        name = random.choice(self.config["OTP"]["name"])

        # Generate the OTP
        self.OTP_first_file, self.OTP_second_file = self.OTP.generate(
            version=version,
            firmware=firmware,
            body=body,
            connect=connect,
            display=display,
            color=color,
            region=region,
            name=name,
            output_dir="assets/otp/",
            base_name="",
        )

    def flash_OTP(self, config):
        self.logger.info("Trying to flash OTP")

        if self.OTP_first_file is None or self.OTP_second_file is None:
            raise Exception("OTP files were not generated!")

        # Flash all OTP files
        self.OTP.flash_all(
            first_file=self.OTP_first_file,
            second_file=self.OTP_second_file,
            first_address=self._to_int(config["first_address"]),
            second_address=self._to_int(config["second_address"]),
        )

    def flash_core2_fus(self, config):
        self.logger.info("Trying to flash Core2 FUS")

        # Get the FUS config
        fus_address = config["address"]
        fus_file = (
            "assets/stm32wb5x_FUS_fw_for_fus_0_5_3.bin"
            if config["from_version"] == "0.5.3"
            else "assets/stm32wb5x_FUS_fw.bin"
        )

        # Flash the FUS
        returncode = self.Flasher.core2fus(fus_address=fus_address, fus_file=fus_file)
        if returncode != 0:
            self.logger.error("Failed to flash Core2 FUS")
            raise Exception("Flash failed")

    def flash_core2_radio(self, config):
        self.logger.info("Trying to flash Core2 Radio")

        # Get the Radio config
        radio_address = config["address"]
        radio_file = "assets/stm32wb5x_BLE_Stack_light_fw.bin"

        # Flash the Radio
        returncode = self.Flasher.core2radio(
            radio_address=radio_address, radio_file=radio_file
        )
        if returncode != 0:
            self.logger.error("Failed to flash Core2 Radio")
            raise Exception("Flash failed")

    def flash_bootloader(self, config):
        self.logger.info("Trying to flash Bootloader")

        bootloader = "assets/bootloader.bin"

        # Flash the bootloader
        returncode = self.Flasher.core1bootloader(
            bootloader=bootloader, address=self.config["bootloader"]["address"]
        )
        if returncode != 0:
            self.logger.error("Failed to flash Core1 bootloader")
            raise Exception("Flash failed")

    def flash_firmware(self, config):
        self.logger.info("Trying to flash firmware")

        firmware = "assets/firmware.bin"

        # Flash the firmware
        returncode = self.Flasher.core1firmware(
            firmware=firmware, address=self.config["firmware"]["address"]
        )
        if returncode != 0:
            self.logger.error("Failed to flash Core1 firmware")
            raise Exception("Flash failed")

    def flash_cks(self, config):
        self.logger.info("Trying to flash CKS")

        key_list = {
            "key_master.bin": "2",
            "key_1.bin": "3",
            "key_2.bin": "3",
            "key_3.bin": "3",
            "key_4.bin": "3",
            "key_5.bin": "3",
            "key_6.bin": "3",
            "key_7.bin": "3",
            "key_8.bin": "3",
            "key_9.bin": "3",
            "key_10.bin": "3",
        }

        # key_list_unencrypted = {
        #     "key_master.bin": "2",
        #     "key_unencrypted_1.bin": "1",
        #     "key_unencrypted_2.bin": "1",
        #     "key_unencrypted_3.bin": "1",
        #     "key_unencrypted_4.bin": "1",
        #     "key_unencrypted_5.bin": "1",
        #     "key_unencrypted_6.bin": "1",
        #     "key_unencrypted_7.bin": "1",
        #     "key_unencrypted_8.bin": "1",
        #     "key_unencrypted_9.bin": "1",
        #     "key_unencrypted_10.bin": "1",
        # }

        for i in key_list.keys():
            self.logger.debug(i)
            if (
                subprocess.run(
                    [
                        "STM32_Programmer_CLI",
                        "-c",
                        "port=SWD",
                        "freq=24000",
                        "-wusrkey",
                        f"assets/cks/{i}",
                        f"keytype={key_list[i]}",
                    ]
                ).returncode
                != 0
            ):
                self.logger.error(f"Failed to flash CKS, {i}")
                raise Exception("Flash failed")

    def generate_cks(self):
        self.logger.info("Trying to generate CKS")

        os.makedirs("assets/cks", exist_ok=True)
        # Generate the raw keys
        master_key: str = os.urandom(16).hex().upper()
        encrypted_keys_unencrypted: list[str] = [
            os.urandom(32).hex().upper() for _ in range(10)
        ]

        self.logger.info(f"Master key: {master_key}")
        self.logger.info(f"Encrypted keys (unencrypted):")
        for i, key in enumerate(encrypted_keys_unencrypted):
            self.logger.info(f"{i+1}. {key}")

        # Encrypt the keys
        encrypted_keys = []
        for i in range(len(encrypted_keys_unencrypted)):
            encrypted_keys_unencrypted_bytes = bytes.fromhex(
                encrypted_keys_unencrypted[i]
            )
            encrypted_iv = self.encrypted_key_iv[i]
            encrypted_key = self.aes128gcm_encrypt(
                bytes().fromhex(master_key),
                bytes(encrypted_iv + [0x00, 0x00, 0x00, 0x02]),
                encrypted_keys_unencrypted_bytes,
            )

            encrypted_keys.append(encrypted_key.hex().upper())
            with open("assets/cks/key_master.bin", "wb") as f:
                f.write(bytes().fromhex(master_key))

            with open(f"assets/cks/key_{i+1}.bin", "wb") as f:
                f.write(bytes([0x03]))  # Byte0: 0x03 (type=encrypted)
                f.write(
                    bytes([0x20])
                )  # Byte1: 0x20 (size of the key: 32 bytes, 256 bits)
                f.write(encrypted_key)  # Byte2-Byte33: KeyData[0]-KeyData[31]
                f.write(bytes(encrypted_iv))  # Byte34-Byte45: IV[0]-IV[11]

        self.logger.debug(f"Encrypted keys:\n{encrypted_keys}\n")

    def run(self):
        self.logger.info(banner)

        if self.config["OTP"]["generate_new"]:
            self.generate_OTP()

        if self.config["CKS"]["generate_new"]:
            self.generate_cks()

        try:
            if self.config["OTP"]["flash"]:
                self.flash_OTP(self.config["OTP"])
            if self.config["FUS"]["flash"]:
                self.flash_core2_fus(self.config["FUS"])
            if self.config["radio"]["flash"]:
                self.flash_core2_radio(self.config["radio"])
            if self.config["CKS"]["flash"]:
                self.flash_cks(self.config["CKS"])
            if self.config["bootloader"]["flash"]:
                self.flash_bootloader(self.config["bootloader"])
            if self.config["firmware"]["flash"]:
                self.flash_firmware(self.config["firmware"])

            self.logger.info(finish_banner)

        except Exception as e:
            self.logger.error(f"Flash failed: {e}")


if __name__ == "__main__":
    FactoryFlasher().run()
