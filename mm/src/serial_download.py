import serial, serial.tools.list_ports
from time import sleep
from pathlib import Path
from tqdm import tqdm
from zlib import crc32
import log


SERIAL_PORT = None
SERIAL_INIT_BAUDRATE = 115200
SERIAL_PORT_READ_TIMEOUT = 2

MAX_PAYLOAD_LENGTH = 65536




FRAME_PREAMBLE = bytes([0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x5D])

SYNC_TAG   = 0x00000008
CHANGE_BAUDRATE_TAG   = 0x0000000F
VERSION_TAG = 0x00000020
EXECUTE_TAG = 0x00000021
REBOOT_TAG = 0x00000022

MEM_BEGIN_TAG   = 0x00000005
MEM_END_TAG     = 0x00000006
MEM_DATA_TAG    = 0x00000007

FLASH_BEGIN_TAG   = 0x00000030
FLASH_END_TAG     = 0x00000031
FLASH_DATA_TAG    = 0x00000032

FS_BEGIN_TAG   = 0x00000033
FS_END_TAG     = 0x00000034
FS_DATA_TAG    = 0x00000035




def get_uint32_big_bytes(number):
    if not isinstance(number, int) or number > 0xFFFFFFFF:
        log.dbg('only support 32bit number!')
    
    return number.to_bytes(4, byteorder='big')

def find_serial_device(device_name):
    port_list = list(serial.tools.list_ports.grep(device_name))
    if len(port_list) > 1:
        log.wrn('found more than one ' + device_name + '!')
        port_path = None
    elif len(port_list) == 0:
        port_path = None
    else:
        port_path = port_list[0].device

    return port_path


def init_serial_device(device_name):
    global SERIAL_PORT

    port_path = find_serial_device(device_name)
    if port_path is None:
        log.die('plz make sure ' + device_name + ' is correctly connected to your computer!')
    else:
        log.inf('Found ' + device_name + ' at ' + port_path)

    SERIAL_PORT = serial.Serial(port_path, SERIAL_INIT_BAUDRATE, 8, 'N', 1)

    if SERIAL_PORT is not None and SERIAL_PORT.is_open:
        SERIAL_PORT.timeout = SERIAL_PORT_READ_TIMEOUT
        SERIAL_PORT.reset_output_buffer()
        SERIAL_PORT.reset_input_buffer()
        log.inf('Open ' + device_name + ' success')
    else:
        log.die('Open ' + device_name + ' failed!')
    


def deinit_serial_device():
    if SERIAL_PORT is not None and SERIAL_PORT.is_open:
        SERIAL_PORT.close()


def reset_to_download():
    SERIAL_PORT.dtr = False    #DTR = 1, RTS = 1 | BOOT = Pullup,   RESET = Pullup,
    SERIAL_PORT.rts = True     #DTR = 1, RTS = 0 | BOOT = Pullup,   RESET = 0,
    sleep(0.05)


    SERIAL_PORT.dtr = True     #DTR = 0, RTS = 0 | BOOT = Pullup, RESET = Charging,
    # Large capacitor at RESET pin
    SERIAL_PORT.rts = False    #DTR = 0, RTS = 1 | BOOT = 0,      RESET = From 0 to Pullup,
    sleep(0.05)

    SERIAL_PORT.dtr = False    #DTR = 1, RTS = 1 | BOOT = Pullup, RESET = Pullup,
    sleep(0.05)           #Wait MCU serial port ready




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
        log.dbg('Response error: error happend')
        log.dbg('')
        return False

    if tag[3] != req_tag[3]:
        log.dbg('Response error: response id not equal')
        log.dbg('')
        return False


    return True


def response_get_payload(response):
    return response[8:-4]


def sync(try_count = 6):
    count = 0
    success = False
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
            success = True
            break
        else:
            sleep(0.1)
    
    print('', flush=True)
    SERIAL_PORT.timeout = previous_timeout
    if not success:
        log.die('serial port synchronization failed!')



def mem_begin(target_addr, target_length):
    payload = get_uint32_big_bytes(target_addr) + get_uint32_big_bytes(target_length)

    send_request(MEM_BEGIN_TAG, payload)
    response = wait_response()
    if not response_verify(response, MEM_BEGIN_TAG):
        log.dbg('mem_begin failed')


def mem_data(payload):
    send_request(MEM_DATA_TAG, payload)
    response = wait_response()
    if not response_verify(response, MEM_DATA_TAG):
        log.dbg('mem_data failed')



def mem_end(bin_crc):
    payload = get_uint32_big_bytes(bin_crc)

    send_request(MEM_END_TAG, payload)
    response = wait_response()
    if not response_verify(response, MEM_END_TAG):
        log.dbg('mem_end failed')

def flash_begin(image_offset, image_length):
    image_offset = get_uint32_big_bytes(image_offset)
    image_length = get_uint32_big_bytes(image_length)

    payload = image_offset + image_length

    send_request(FLASH_BEGIN_TAG, payload)
    response = wait_response()
    if not response_verify(response, FLASH_BEGIN_TAG):
        log.dbg('flash_begin failed!')


def flash_data(payload):
    send_request(FLASH_DATA_TAG, payload)
    response = wait_response()
    if not response_verify(response, FLASH_DATA_TAG):
        log.dbg('flash_data failed!')



def flash_end(bin_crc, run_addr):
    bin_crc = get_uint32_big_bytes(bin_crc)
    run_addr = get_uint32_big_bytes(run_addr)
    payload = bin_crc + run_addr

    send_request(FLASH_END_TAG, payload)
    response = wait_response()
    if not response_verify(response, FLASH_END_TAG):
        log.dbg('flash_end failed')

def sdcard_begin(image_length, image_path):
    image_length = get_uint32_big_bytes(image_length)
    image_path = bytes(image_path, 'utf-8')

    payload = image_length + image_path

    send_request(FS_BEGIN_TAG, payload)
    response = wait_response()
    if not response_verify(response, FS_BEGIN_TAG):
        log.dbg('sdcard_begin failed!')


def sdcard_data(payload):
    send_request(FS_DATA_TAG, payload)
    response = wait_response()
    if not response_verify(response, FS_DATA_TAG):
        log.dbg('sdcard_begin failed!')



def sdcard_end(bin_crc,run_addr):
    bin_crc = get_uint32_big_bytes(bin_crc)
    run_addr = get_uint32_big_bytes(run_addr)

    payload = bin_crc + run_addr

    send_request(FS_END_TAG, payload)
    response = wait_response()
    if not response_verify(response, FS_END_TAG):
        log.dbg('sdcard_end failed!')



def send_file2mem(file_name, addr):
    f = Path(file_name)

    if not f.is_file():
        log.die('open file ' + str(f) + ' failed!')

    file_length = f.stat().st_size
    file_bytes = f.read_bytes()
    file_crc = crc32(file_bytes)

    mem_begin(addr, file_length)

    offset = 0
    while offset < file_length:
        payload = file_bytes[offset : offset + MAX_PAYLOAD_LENGTH]
        offset += MAX_PAYLOAD_LENGTH
        mem_data(payload)
    
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


def send_file2sdcard(file_name, target_name, run_addr):
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
    sdcard_end(file_crc, run_addr)


def get_boot_version():
    send_request(VERSION_TAG)
    response = wait_response()

    if not response_verify(response, VERSION_TAG):
        log.die('failed to get ROM version!')

    payload = response_get_payload(response)
    version = payload.decode('utf-8')
    log.inf('ROM version: ' + version)



def change_host_baud(new_baud):
    SERIAL_PORT.baudrate = new_baud
    sleep(0.01)
    SERIAL_PORT.reset_output_buffer()
    SERIAL_PORT.reset_input_buffer()


def sync_baud(new_baud):
    payload = get_uint32_big_bytes(new_baud)

    sleep(0.01)
    SERIAL_PORT.reset_output_buffer()
    SERIAL_PORT.reset_input_buffer()
    send_request(CHANGE_BAUDRATE_TAG, payload)
    response = wait_response()
    if not response_verify(response, CHANGE_BAUDRATE_TAG):
        log.die('modify baudrate to ' + new_baud + ' failed!')
    SERIAL_PORT.baudrate = new_baud
    sleep(0.01)
    SERIAL_PORT.reset_output_buffer()
    SERIAL_PORT.reset_input_buffer()



def execute(address):
    payload = get_uint32_big_bytes(address)

    send_request(EXECUTE_TAG, payload)
    response = wait_response()
    if not response_verify(response, EXECUTE_TAG):
        log.die('excute at ' + address + ' failed!') 

def reboot(address):
    payload = get_uint32_big_bytes(address)

    send_request(REBOOT_TAG, payload)
    response = wait_response()
    if not response_verify(response, REBOOT_TAG):
        log.die('reboot tag failed')





















def test_list_serial_port():
    port_list = serial.tools.list_ports.comports()
    for port in port_list:
        log.inf(port.description)




SERIAL_DEVICE_NAME = 'USB Single Serial'
# SERIAL_DEVICE_NAME = 'FT232R'
# SERIAL_DEVICE_NAME = 'CP2102N'



def test():
    init_serial_device(SERIAL_DEVICE_NAME)

    reset_to_download()
    sync()

    get_boot_version()

    sync_baud(3000000)
    sync()

    send_file2mem('/home/andy/Documents/recovery/build/zephyr/zephyr.bin', 0x20200000)
    execute(0x20200000)

    sleep(0.1)
    sync()

    # send_file2flash('/home/andy/Documents/recovery/recovery-bootloader/zephyr.bin', 0x00000000, 0x60100000)
    send_file2sdcard('/home/andy/Documents/recovery/recovery-bootloader/red_blue.bin', 'feather.bin', 0x80000000)

    reboot(0x00000000)

    deinit_serial_device()




#log.set_verbosity(log.VERBOSE_DBG)
#test_list_serial_port()
test()