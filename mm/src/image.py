from pathlib import Path
from zlib import crc32
import log, util


IMAGE_HEADER_CAPACITY = 1024 * 4

IMAGE_START_OFFSET = IMAGE_HEADER_CAPACITY  # Default 4k offset
IMAGE_LOAD_ADDRESS = 0x80000000             # SDRAM start address
IMAGE_TYPE = 0x20                           # User app 0
IMAGE_VERIFY_TYPE = 0x01                    # CRC32
IMAGE_VERIFY_CAPACITY = 64                  # 64 bytes capacity

def create_image(bin_path, out_path, out_name, load_address=IMAGE_LOAD_ADDRESS):
    image_name = out_name
    image_path = out_path / image_name

    log.inf('Creating image ' + image_name + '...')

    image_raw_binary = bin_path.read_bytes()

    image_offset = IMAGE_START_OFFSET.to_bytes(8, byteorder='little')
    image_size = len(image_raw_binary).to_bytes(8, byteorder='little')
    image_load_address = load_address.to_bytes(8, byteorder='little')
    image_type = IMAGE_TYPE.to_bytes(4, byteorder='little')
    image_verify_type = IMAGE_VERIFY_TYPE.to_bytes(4, byteorder='little')
    image_crc = crc32(image_raw_binary).to_bytes(4, byteorder='little')
    image_crc = image_crc + bytes(IMAGE_VERIFY_CAPACITY - len(image_crc))

    image_header = image_offset + image_size + image_load_address + image_type + image_verify_type + image_crc

    header_crc = crc32(image_header).to_bytes(4, byteorder='little')
    image_header = header_crc + image_header

    header_block = image_header.ljust(IMAGE_HEADER_CAPACITY, b'\xff')

    image_path.write_bytes(header_block + image_raw_binary)