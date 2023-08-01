from pickletools import read_stringnl_noescape
import serial, serial.tools.list_ports
from time import sleep
from pathlib import Path
from tqdm import tqdm
from zlib import crc32
import log, util


SERIAL_PORT = None
SERIAL_INIT_BAUDRATE = 115200
SERIAL_PORT_READ_TIMEOUT = 2

MAX_PAYLOAD_LENGTH = 65536


FRAME_PREAMBLE = bytes([0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x5D])

SYNC_TAG            = 0x02
INFO_TAG            = 0x03
VERSION_TAG         = 0x04
REBOOT_TAG          = 0x05
EXECUTE_TAG         = 0x06
CHANGE_BAUDRATE_TAG = 0x07
READ_TAG            = 0x08
WRITE_TAG           = 0x09
RAM_BEGIN_TAG       = 0x0A
RAM_DATA_TAG        = 0x0B
RAM_END_TAG         = 0x0C
VERIFY_TAG          = 0x0D

FLASH_BEGIN_TAG     = 0x30
FLASH_DATA_TAG      = 0x31
FLASH_END_TAG       = 0x32

PARTION_BEGIN_TAG   = 0x38
PARTION_DATA_TAG    = 0x39
PARTION_END_TAG     = 0x3A
PARTION_SETBOOT_TAG = 0x3B

FS_BEGIN_TAG        = 0x40
FS_DATA_TAG         = 0x41
FS_END_TAG          = 0x42




def get_uint32_big_bytes(number):
    if not isinstance(number, int) or number > 0xFFFFFFFF:
        log.dbg('only support 32bit number!')
    
    return number.to_bytes(4, byteorder='big')


def get_uint64_big_bytes(number):
    if not isinstance(number, int):
        log.dbg('only support 64bit int number!')
    
    return number.to_bytes(8, byteorder='big')


def find_serial_device(device_name):
    port_list = list(serial.tools.list_ports.grep(device_name))
    port_path_list = list()
    for port in port_list:
        port_path_list.append(port.device)
    
    if len(port_path_list) == 0:
        port_path_list = None

    return port_path_list


def init_serial_device(device_name):
    global SERIAL_PORT

    port_path_list = find_serial_device(device_name)

    if port_path_list is None:
        log.die('Please confirm ' + device_name + ' is correctly connected to your computer!')
    elif len(port_path_list) > 1:
        log.wrn('Found more than one ' + device_name)

    for port_path in port_path_list:
        try:
            SERIAL_PORT = serial.Serial(port_path, SERIAL_INIT_BAUDRATE, 8, 'N', 1)
        except IOError:
            log.wrn('Device or resource busy! Plz make sure it is not in use!')

        if SERIAL_PORT is not None and SERIAL_PORT.is_open:
            SERIAL_PORT.timeout = SERIAL_PORT_READ_TIMEOUT
            SERIAL_PORT.reset_output_buffer()
            SERIAL_PORT.reset_input_buffer()
            if len(port_path_list) > 1:
                reset_to_download()
                ret = sync(3)
                if ret:
                    SERIAL_PORT.reset_output_buffer()
                    SERIAL_PORT.reset_input_buffer()
                    log.inf('Open ' + port_path + ' success')
                    break
                else:
                    deinit_serial_device()
            else:
                log.inf('Open ' + port_path + ' success')
        else:
            log.wrn('Open ' + port_path + ' failed!')
    
    if SERIAL_PORT is None or not SERIAL_PORT.is_open:
        log.die('Open ' + device_name + ' failed!')
    


def deinit_serial_device():
    if SERIAL_PORT is not None and SERIAL_PORT.is_open:
        SERIAL_PORT.close()


def reset_to_download():
    SERIAL_PORT.dtr = False    #DTR = 1, RTS = 1 | BOOT = Pullup,   RESET = Pullup,
    SERIAL_PORT.rts = True     #DTR = 1, RTS = 0 | BOOT = Pullup,   RESET = 0,
    sleep(0.04)

    SERIAL_PORT.dtr = True     #DTR = 0, RTS = 0 | BOOT = Pullup, RESET = Charging,
    # Large capacitor at RESET pin
    SERIAL_PORT.rts = False    #DTR = 0, RTS = 1 | BOOT = 0,      RESET = From 0 to Pullup,
    sleep(0.06)                # ~0.01: EN pull up done; ~0.02: ROM init done; ~0.04: info output done

    SERIAL_PORT.dtr = False    #DTR = 1, RTS = 1 | BOOT = Pullup, RESET = Pullup,





def send_request(tag, payload = None):
    if not isinstance(tag, int):
        log.dbg('tag must be 32bit int')
        exit(1)
    
    if payload == None:
        tag = get_uint32_big_bytes(tag)
        length = get_uint32_big_bytes(0)
        crc =  get_uint32_big_bytes(crc32(tag + length))
        log.dbg('request:')
        log.dbg('    tag: 0x' + tag.hex())
        log.dbg('    length: 0x' + length.hex())
        log.dbg('    payload: None')
        log.dbg('    crc: 0x' + crc.hex())
        SERIAL_PORT.write(FRAME_PREAMBLE + tag + length + crc)
    else:
        if not isinstance(payload, bytes) and not isinstance(payload, bytearray):
            log.dbg('payload must be bytes or bytearray')
            exit(1)
        tag = get_uint32_big_bytes(tag)
        length = get_uint32_big_bytes(len(payload))
        crc =  get_uint32_big_bytes(crc32(tag + length + payload))
        log.dbg('request:')
        log.dbg('    tag: 0x' + tag.hex())
        log.dbg('    length: 0x' + length.hex())
        log.dbg('    payload: ' + str(int.from_bytes(length, 'big', signed='False')) + 'bytes')
        log.dbg('    crc: 0x' + crc.hex())
        SERIAL_PORT.write(FRAME_PREAMBLE + tag + length + payload + crc)

def wait_response():
    header = SERIAL_PORT.read(16)

    if not header.startswith(FRAME_PREAMBLE) or len(header) != 16:
        log.dbg('response: ')
        log.dbg('    Header transfer error!')
        return None

    payload_length = int.from_bytes(header[12:16], 'big', signed='False')
    rest = SERIAL_PORT.read(payload_length + 4)
    if len(rest) != payload_length + 4:
        log.dbg('response: ')
        log.dbg('    Need: ' + str(payload_length + 4) + ' Received: ' + str(len(rest)))
        return None

    response = header[8:] + rest
    return response

def response_check_crc(response):   
    tag = response[0:4]
    length = response[4:8]
    payload = response[8:-4]
    payload_length = int.from_bytes(length, 'big', signed='False')
    crc = response[-4:]

    log.dbg('response: ')
    log.dbg('    tag: 0x' + tag.hex())
    log.dbg('    length: 0x' + length.hex())
    log.dbg('    payload: ' + payload.hex())
    log.dbg('    crc: 0x' + crc.hex())
    log.dbg('')

    cal_crc = get_uint32_big_bytes(crc32(tag + length + payload))

    return crc == cal_crc


def response_verify(response, req_tag):
    req_tag = get_uint32_big_bytes(req_tag)

    if response == None:
        log.dbg('Response error: response is None')
        log.dbg(' ')
        return False

    if not response_check_crc(response):
        log.dbg('Response error: response crc not match')
        log.dbg(' ')
        return False
    
    response_byte = 0x80
    success_byte = 0x00
    
    tag = response[0:4]

    if tag[0] != response_byte:
        log.dbg('Response error: not a response')
        log.dbg('')
        return False

    if tag[1] != success_byte:
        log.dbg('Response error: error happend: ' + str(tag[1]))
        log.dbg('')
        return False

    if tag[3] != req_tag[3]:
        log.dbg('tag[3] = ' + str(tag[3]))
        log.dbg('req_tag[3] = ' + str(req_tag[3]))
        log.dbg('Response error: response id not equal')
        log.dbg('')
        return False

    return True


def response_get_payload(response):
    return response[8:-4]


def sync(try_count = 6):
    count = 0
    result = False
    previous_timeout = SERIAL_PORT.timeout
    
    SERIAL_PORT.timeout = 0.2
    print('Serial port synchronizing', end = '', flush = True)
    while count < try_count:
        count += 1
        print('.', end = '', flush = True)
        SERIAL_PORT.reset_output_buffer()
        SERIAL_PORT.reset_input_buffer()
        send_request(SYNC_TAG)
        response = wait_response()

        if response_verify(response, SYNC_TAG):
            result = True
            break
        else:
            sleep(0.1)
    
    print('', flush=True)
    SERIAL_PORT.timeout = previous_timeout
    if not result:
        log.wrn('serial port synchronization failed!')

    return result



def mem_begin(target_addr, target_length):
    payload = get_uint64_big_bytes(target_addr) + get_uint32_big_bytes(target_length)

    send_request(RAM_BEGIN_TAG, payload)
    response = wait_response()
    if not response_verify(response, RAM_BEGIN_TAG):
        log.die('mem_begin failed')


def mem_data(payload):
    send_request(RAM_DATA_TAG, payload)
    response = wait_response()
    if not response_verify(response, RAM_DATA_TAG):
        log.die('mem_data failed')



def mem_end(bin_crc):
    payload = get_uint32_big_bytes(bin_crc)

    send_request(RAM_END_TAG, payload)
    response = wait_response()
    if not response_verify(response, RAM_END_TAG):
        log.die('mem_end failed')


def flash_begin(image_offset, image_length):
    image_offset = get_uint64_big_bytes(image_offset)
    image_length = get_uint32_big_bytes(image_length)

    payload = image_offset + image_length

    send_request(FLASH_BEGIN_TAG, payload)
    response = wait_response()
    if not response_verify(response, FLASH_BEGIN_TAG):
        log.die('flash_begin failed!')


def flash_data(payload):
    send_request(FLASH_DATA_TAG, payload)
    response = wait_response()
    if not response_verify(response, FLASH_DATA_TAG):
        log.die('flash_data failed!')


def flash_end(bin_crc):
    bin_crc = get_uint32_big_bytes(bin_crc)
    payload = bin_crc

    send_request(FLASH_END_TAG, payload)
    response = wait_response()
    if not response_verify(response, FLASH_END_TAG):
        log.die('flash_end failed')



def partion_begin(name, image_length):
    name = bytes(name, 'utf-8').ljust(64, b'\x00')
    image_length = get_uint32_big_bytes(image_length)

    payload = name + image_length

    send_request(PARTION_BEGIN_TAG, payload)
    response = wait_response()
    if not response_verify(response, PARTION_BEGIN_TAG):
        log.die('partion_begin failed!')


def partion_data(payload):
    send_request(PARTION_DATA_TAG, payload)
    response = wait_response()
    if not response_verify(response, PARTION_DATA_TAG):
        log.die('partion_data failed!')


def partion_end(bin_crc):
    bin_crc = get_uint32_big_bytes(bin_crc)
    payload = bin_crc

    send_request(PARTION_END_TAG, payload)
    response = wait_response()
    if not response_verify(response, PARTION_END_TAG):
        log.die('partion_end failed')


def partion_set_boot(name):
    payload = bytes(name, 'utf-8').ljust(64, b'\x00')

    log.dbg(payload.hex())

    send_request(PARTION_SETBOOT_TAG, payload)
    response = wait_response()
    if not response_verify(response, PARTION_SETBOOT_TAG):
        log.die('set boot partion failed!')




def sdcard_begin(image_length, image_path):
    image_length = get_uint32_big_bytes(image_length)
    image_path = bytes(image_path, 'utf-8')

    payload = image_length + image_path

    send_request(FS_BEGIN_TAG, payload)
    response = wait_response()
    if not response_verify(response, FS_BEGIN_TAG):
        log.die('sdcard_begin failed!')


def sdcard_data(payload):
    send_request(FS_DATA_TAG, payload)
    response = wait_response()
    if not response_verify(response, FS_DATA_TAG):
        log.die('sdcard_begin failed!')



def sdcard_end(bin_crc):
    bin_crc = get_uint32_big_bytes(bin_crc)

    payload = bin_crc

    send_request(FS_END_TAG, payload)
    response = wait_response()
    if not response_verify(response, FS_END_TAG):
        log.die('sdcard_end failed!')



def send_file2mem(file_name, addr, bar=False):
    f = Path(file_name)

    if not f.is_file():
        log.die('open file ' + str(f) + ' failed!')

    file_length = f.stat().st_size
    file_bytes = f.read_bytes()
    file_crc = crc32(file_bytes)
    if bar:
        process_bar = tqdm(total=file_length, unit='B', unit_scale=True)

    mem_begin(addr, file_length)

    offset = 0
    while offset < file_length:
        payload = file_bytes[offset : offset + MAX_PAYLOAD_LENGTH]
        offset += MAX_PAYLOAD_LENGTH
        mem_data(payload)
        if bar:
            process_bar.update(len(payload))

    if bar:
        process_bar.close()
    mem_end(file_crc)


def send_file2flash(file_name, addr, run_addr):
    f = Path(file_name)

    if not f.is_file():
        log.die('open file ' + str(f) + ' failed!')

    file_length = f.stat().st_size
    file_bytes = f.read_bytes()
    file_crc = crc32(file_bytes)
    process_bar = tqdm(total=file_length, unit='B', unit_scale=True)

    flash_begin(addr, file_length)

    offset = 0
    while offset < file_length:
        payload = file_bytes[offset : offset + MAX_PAYLOAD_LENGTH]
        offset += MAX_PAYLOAD_LENGTH
        flash_data(payload)
        process_bar.update(len(payload))

    process_bar.close()
    flash_end(file_crc, run_addr)


def send_file2sdcard(file_name, target_name):
    f = Path(file_name)

    if not f.is_file():
        log.die('open file ' + str(f) + ' failed!')

    file_length = f.stat().st_size
    file_bytes = f.read_bytes()
    file_crc = crc32(file_bytes)
    process_bar = tqdm(total=file_length, unit='B', unit_scale=True)

    sdcard_begin(file_length, target_name)

    offset = 0
    while offset < file_length:
        payload = file_bytes[offset : offset + MAX_PAYLOAD_LENGTH]
        offset += MAX_PAYLOAD_LENGTH
        sdcard_data(payload)
        process_bar.update(len(payload))
    
    process_bar.close()
    sdcard_end(file_crc)


def send_file2partion(file_name, partition_name):
    f = Path(file_name)

    if not f.is_file():
        log.die('open file ' + str(f) + ' failed!')

    file_length = f.stat().st_size
    file_bytes = f.read_bytes()
    file_crc = crc32(file_bytes)
    process_bar = tqdm(total=file_length, unit='B', unit_scale=True)

    partion_begin(partition_name, file_length)

    offset = 0
    while offset < file_length:
        payload = file_bytes[offset : offset + MAX_PAYLOAD_LENGTH]
        offset += MAX_PAYLOAD_LENGTH
        partion_data(payload)
        process_bar.update(len(payload))

    process_bar.close()
    partion_end(file_crc)


def get_board_info():
    send_request(INFO_TAG)
    response = wait_response()

    if not response_verify(response, INFO_TAG):
        log.die('get board info failed')

    payload = response_get_payload(response)
    info = payload.decode('utf-8')
    log.inf('Board info: ' + info)


def get_rom_version():
    send_request(VERSION_TAG)
    response = wait_response()

    if not response_verify(response, VERSION_TAG):
        log.die('get ROM version failed')

    payload = response_get_payload(response)
    major = str(payload[1])
    minor = str(payload[2])
    patch = str(payload[3])
    log.inf('ROM_Version: ' + major + '.' + minor + '.' + patch)

def change_host_baud(new_baud):
    SERIAL_PORT.baudrate = new_baud
    sleep(0.01)
    SERIAL_PORT.reset_output_buffer()
    SERIAL_PORT.reset_input_buffer()


def sync_baud(new_baud):
    payload = get_uint32_big_bytes(new_baud)

    SERIAL_PORT.reset_output_buffer()
    SERIAL_PORT.reset_input_buffer()
    send_request(CHANGE_BAUDRATE_TAG, payload)
    response = wait_response()
    if not response_verify(response, CHANGE_BAUDRATE_TAG):
        log.die('modify baudrate to ' + str(new_baud) + ' failed!')
    SERIAL_PORT.baudrate = new_baud
    sleep(0.01)
    SERIAL_PORT.reset_output_buffer()
    SERIAL_PORT.reset_input_buffer()


def execute(address):
    payload = get_uint64_big_bytes(address)

    send_request(EXECUTE_TAG, payload)
    response = wait_response()
    if not response_verify(response, EXECUTE_TAG):
        log.die('excute at ram address ' + str(address) + ' failed!') 

def reboot():
    send_request(REBOOT_TAG)
    response = wait_response()
    if not response_verify(response, REBOOT_TAG):
        log.die('reboot tag failed')





















def test_list_serial_port():
    port_list = serial.tools.list_ports.comports()
    for port in port_list:
        log.inf(port.device)
        log.inf(port.description)


def load_to_ram(serial_name, image, address):
    init_serial_device(serial_name)

    reset_to_download()
    if sync() == False:
        log.die("Sync failed!")

    sync_baud(3000000)
    if sync() == False:
        log.die("Sync failed!")

    send_file2mem(image, address)
    execute(address)

    deinit_serial_device()


def load_to_partition(serial_name, image, partition):
    init_serial_device(serial_name)

    reset_to_download()
    if sync() == False:
        log.die("Sync failed!")

    sync_baud(3000000)
    if sync() == False:
        log.die("Sync failed!")

    get_board_info()
    get_rom_version()

    serial_loader = util.get_tool_path('serial-loader')
    send_file2mem(serial_loader, 0x00000000)
    execute(0x00000000)

    sleep(0.05)
    if sync() == False:
        log.die("Sync failed!")

    send_file2partion(image, partition)

    partion_set_boot(partition)

    reboot()

    deinit_serial_device()


def load_to_sdcard(serial_name, image, target_name):
    init_serial_device(serial_name)

    reset_to_download()
    if sync() == False:
        log.die("Sync failed!")

    sync_baud(3000000)
    if sync() == False:
        log.die("Sync failed!")

    get_board_info()


    serial_loader = util.get_tool_path('serial-loader')
    send_file2mem(serial_loader, 0x00000000)
    execute(0x00000000)

    sleep(0.05)
    if sync() == False:
        log.die("Sync failed!")

    send_file2sdcard(image, target_name)
    reboot()

    deinit_serial_device()



IMAGE1 = Path('./micro.img')
IMAGE2 = Path('./clear_to_AA.bin')

def test_load_to_ram(serial_name, address):

    init_serial_device(serial_name)
    count = 0
    mbytes = 0

    i1_size = IMAGE1.stat().st_size / 1024 / 1024.0
    i2_size = IMAGE2.stat().st_size / 1024 / 1024.0

    while True:
        change_host_baud(115200)
        reset_to_download()
        sync()

        sync_baud(3000000)
        sync()

        if count % 2 == 0:
            send_file2mem(IMAGE2, address, True)
            mbytes += i2_size
        else:
            send_file2mem(IMAGE1, address, True)
            mbytes += i1_size
        
        #deinit_serial_device()
        count += 1

        log.inf('------ count = ' + str(count) + ' transfer ' + str(mbytes) + 'mb' + ' ------')


#log.set_verbosity(log.VERBOSE_DBG)
#test_load_to_ram('wch', 0x80000000)
