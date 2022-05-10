from pathlib import Path
import util, log, mmp

import os, serial, time
import serial.tools.list_ports
from zlib import crc32


SERIAL_INIT_BAUDRATE = 115200
SERIAL_PORT_READ_TIMEOUT = 2

frame_header = bytearray([0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x5D])


mem_begin_tag   = 0x00000005
mem_end_tag     = 0x00000006
mem_data_tag    = 0x00000007

flash_begin_tag   = 0x00000030
flash_end_tag     = 0x00000031
flash_data_tag    = 0x00000032

sdcard_begin_tag   = 0x00000033
sdcard_end_tag     = 0x00000034
sdcard_data_tag    = 0x00000035


sync_tag   = 0x00000008

baud_tag   = 0x0000000F

version_tag = 0x00000020
execute_tag = 0x00000021
reboot_tag = 0x00000022





def get_uint32_big_array(number):
    if not isinstance(number, int) or number > 0xFFFFFFFF:
        log.die('only support 32bit number!')
    
    return bytearray((number).to_bytes(4, byteorder='big'))

def find_serial_device(device_name):
    port_list = list(serial.tools.list_ports.grep(device_name))
    if len(port_list) == 0:
        log.die('cannot find USB to serial device: ' + device_name)

    if len(port_list) > 1:
        log.die('found more than one ' + device_name + ', this is not supported now!')

    port_path = port_list[0].device
    log.inf('Found ' + device_name + ' at ' + port_path)

    return port_path


def init_serial_device(device_name):
    port_path = find_serial_device(device_name)
    port = serial.Serial(port_path, SERIAL_INIT_BAUDRATE, 8, 'N', 1)

    if port is not None and port.is_open:
        port.timeout = SERIAL_PORT_READ_TIMEOUT
        port.reset_output_buffer()
        port.reset_input_buffer()
        log.inf('Open ' + device_name + ' success')
    else:
        log.die('Open ' + device_name + ' failed!')
    
    return port
    


def deinit_serial_device(port):
    if port is not None and port.is_open:
        port.close()


def reset_to_download(port):
    port.dtr = False    #DTR = 1, RTS = 1 | BOOT = Pullup,   RESET = Pullup,
    port.rts = True     #DTR = 1, RTS = 0 | BOOT = Pullup,   RESET = 0,
    time.sleep(0.5)


    port.dtr = True     #DTR = 0, RTS = 0 | BOOT = Pullup, RESET = Charging,
    # Large capacitor at RESET pin
    port.rts = False    #DTR = 0, RTS = 1 | BOOT = 0,      RESET = From 0 to Pullup,
    time.sleep(0.05)

    port.dtr = False    #DTR = 1, RTS = 1 | BOOT = Pullup, RESET = Pullup,




# def send_request(port, tag, length = None, payload = None):
#     if length == None or payload == None:
#         length = get_uint32_big_array(0)
#         crc =  get_uint32_big_array(crc32(tag + length))
#         print('request:')
#         print('    tag: 0x' + tag.hex())
#         print('    length: 0x' + length.hex())
#         print('    payload: ' + str(int.from_bytes(length, 'big', signed='False')) + 'bytes')
#         print('    crc: 0x' + crc.hex())
#         port.write(frame_header + tag + length + crc)
#     else:
#         crc =  get_uint32_big_array(crc32(tag + length + payload))
#         print('request:')
#         print('    tag: 0x' + tag.hex())
#         print('    length: 0x' + length.hex())
#         print('    payload: ' + str(int.from_bytes(length, 'big', signed='False')) + 'bytes')
#         print('    crc: 0x' + crc.hex())
#         port.write(frame_header + tag + length + payload + crc)


def send_request(port, tag, payload = None):
    if not isinstance(tag, int):
        log.die('tag must be 32bit int')
    
    if payload == None:
        tag = get_uint32_big_array(tag)
        length = get_uint32_big_array(0)
        crc =  get_uint32_big_array(crc32(tag + length))
        print('request:')
        print('    tag: 0x' + tag.hex())
        print('    length: 0x' + length.hex())
        print('    payload: ' + str(int.from_bytes(length, 'big', signed='False')) + 'bytes')
        print('    crc: 0x' + crc.hex())
        port.write(frame_header + tag + length + crc)
    else:
        if not isinstance(payload, bytearray) and not isinstance(payload, bytes):
            log.die('payload must be bytearray')
        tag = get_uint32_big_array(tag)
        length = get_uint32_big_array(len(payload))
        crc =  get_uint32_big_array(crc32(tag + length + payload))
        print('request:')
        print('    tag: 0x' + tag.hex())
        print('    length: 0x' + length.hex())
        print('    payload: ' + str(int.from_bytes(length, 'big', signed='False')) + 'bytes')
        print('    crc: 0x' + crc.hex())
        port.write(frame_header + tag + length + payload + crc)

# def wait_response(port):
#     header = port.read(16)

#     if len(header) != 16:
#         print('response: ')
#         print('    Receive header failed!')
#         print(header)
#         return None

#     if not header.startswith(frame_header):
#         print('response: ')
#         print('    Header transfer error!')
#         return None

#     payload_length = int.from_bytes(header[12:16], 'big', signed='False')
#     rest = port.read(payload_length + 4)
#     if len(rest) != payload_length + 4:
#         print('response: ')
#         print('    Need: ' + str(payload_length + 4) + ' Received: ' + ste(len(rest)))
#         return None

#     response = header[8:] + rest
#     print('response: ' + response.hex())
#     return response



def wait_response(port):
    header = port.read(16)

    if len(header) != 16:
        print('response: ')
        print('    Receive header timeout!')
        print(header)
        return None

    if not header.startswith(frame_header):
        print('response: ')
        print('    Header transfer error!')
        return None

    payload_length = int.from_bytes(header[12:16], 'big', signed='False')
    rest = port.read(payload_length + 4)
    if len(rest) != payload_length + 4:
        print('response: ')
        print('    Need: ' + str(payload_length + 4) + ' Received: ' + ste(len(rest)))
        return None

    response = header[8:] + rest
    print('response: ' + response.hex())
    return response



def response_check_crc(response):   
    tag = response[0:4]
    response = response[4:]

    length = response[0:4]
    response = response[4:]

    payload = response[0:-4]

    payload_length = int.from_bytes(length, 'big', signed='False')
    crc = response[payload_length:]

    print('    tag: 0x' + tag.hex())
    print('    length: 0x' + length.hex())
    print('    payload: ' + str(len(payload)) + 'bytes')
    print('    crc: 0x' + crc.hex())

    cal_crc = get_uint32_big_array(crc32(tag + length + payload))

    print(cal_crc.hex())

    return crc == cal_crc




def response_check_success(response, req_tag):
    if response == None:
        print('Failed: response is None')
        print('')
        return False


    if not response_check_crc(response):
        return False
    
    response_byte = 0x80
    success_byte = 0x00
    
    tag = response[0:4]

    if tag[0] != response_byte:
        print('Failed: not a response')
        print('')
        return False

    if tag[1] != success_byte:
        print('Failed: error happend')
        print('')
        return False

    if tag[3] != req_tag[3]:
        print('Failed: response id not equal')
        print('')
        return False


    print('OK!')
    print('')
    return True



def response_verify(response, req_tag):
    req_tag = get_uint32_big_array(req_tag)

    if response == None:
        print('Failed: response is None')
        print('')
        return False


    if not response_check_crc(response):
        return False
    
    response_byte = 0x80
    success_byte = 0x00
    
    tag = response[0:4]

    if tag[0] != response_byte:
        print('Failed: not a response')
        print('')
        return False

    if tag[1] != success_byte:
        print('Failed: error happend')
        print('')
        return False

    if tag[3] != req_tag[3]:
        print('Failed: response id not equal')
        print('')
        return False


    print('OK!')
    print('')
    return True


def response_get_payload(response):
    tag = response[0:4]
    response = response[4:]

    length = response[0:4]
    response = response[4:]

    payload = response[0:-4]
    return payload


def sync(port, try_count = 6):
    count = 0
    success = False
    previous_timeout = port.timeout
    
    port.timeout = 0.4
    print('Serial port synchronizing', end = '')
    while count < try_count:
        count += 1
        print('.', end = '')
        port.reset_output_buffer()
        port.reset_input_buffer()
        send_request(port, sync_tag)
        response = wait_response(port)

        if response_verify(response, sync_tag):
            success = True
            break
        else:
            time.sleep(0.1)
    
    port.timeout = previous_timeout
    print('')
    if not success:
        log.die('serial port synchronization failed!')



def mem_begin(port, target_addr, target_length):
    payload = get_uint32_big_array(target_addr) + get_uint32_big_array(target_length)

    send_request(port, mem_begin_tag, payload)
    response = wait_response(port)
    if not response_verify(response, mem_begin_tag):
        log.die('mem_begin failed')


def mem_data(port, payload):
    send_request(port, mem_data_tag, payload)
    response = wait_response(port)
    if not response_verify(response, mem_data_tag):
        log.die('mem_data failed')



def mem_end(port, bin_crc):
    payload = get_uint32_big_array(bin_crc)

    send_request(port, mem_end_tag, payload)
    response = wait_response(port)
    if not response_verify(response, mem_end_tag):
        log.die('mem_end failed')

def flash_begin(image_offset, image_length):
    image_offset = get_uint32_big_array(image_offset)
    image_length = get_uint32_big_array(image_length)

    payload = image_offset + image_length
    length = get_uint32_big_array(len(payload))

    send_request(port, flash_begin_tag, length, payload)
    response = wait_response(port)
    if not response_check_success(response, flash_begin_tag):
        exit(1)


def flash_data(payload_length, payload):
    send_request(port, flash_data_tag, payload_length, payload)
    response = wait_response(port)
    if not response_check_success(response, flash_data_tag):
        exit(1)



def flash_end(bin_crc,run_addr):
    bin_crc = get_uint32_big_array(bin_crc)
    run_addr = get_uint32_big_array(run_addr)
    payload = bin_crc + run_addr
    length = get_uint32_big_array(len(payload))

    send_request(port, flash_end_tag, length, payload)
    response = wait_response(port)
    if not response_check_success(response, flash_end_tag):
        exit(1)

def sdcard_begin(image_length, image_path):
    image_length = get_uint32_big_array(image_length)
    image_path = bytearray(image_path, 'utf-8')

    payload = image_length + image_path
    length = get_uint32_big_array(len(payload))

    send_request(port, sdcard_begin_tag, length, payload)
    response = wait_response(port)
    if not response_check_success(response, sdcard_begin_tag):
        exit(1)


def sdcard_data(payload_length, payload):
    send_request(port, sdcard_data_tag, payload_length, payload)
    response = wait_response(port)
    if not response_check_success(response, sdcard_data_tag):
        exit(1)



def sdcard_end(bin_crc,run_addr):
    bin_crc = get_uint32_big_array(bin_crc)
    run_addr = get_uint32_big_array(run_addr)
    payload = bin_crc + run_addr
    length = get_uint32_big_array(len(payload))

    send_request(port, sdcard_end_tag, length, payload)
    response = wait_response(port)
    if not response_check_success(response, sdcard_end_tag):
        exit(1)


def send_file2mem(port, file_name, addr):
    f = open(file_name, 'rb')
    file_length = os.path.getsize(file_name)
    bytes_left = file_length
    max_length = 65536
    file_crc = crc32(f.read(file_length))

    mem_begin(port, addr, file_length)

    f.seek(0, 0)
    count = 0
    while bytes_left > 0:
        if bytes_left > max_length:
            size = max_length
        else:
            size = bytes_left
        bytes_left -= size
        count += 1

        length = size
        payload = f.read(size)

        print('write count: ' + str(count))
        mem_data(port, payload)
    f.close()

    mem_end(port, file_crc)

def send_file2flash(file_name, addr, run_addr):
    f = open(file_name, 'rb')
    file_length = os.path.getsize(file_name)
    bytes_left = file_length
    max_length = 65536
    file_crc = crc32(f.read(file_length))

    flash_begin(addr, file_length)

    f.seek(0, 0)
    count = 0
    while bytes_left > 0:
        if bytes_left > max_length:
            size = max_length
        else:
            size = bytes_left
        bytes_left -= size
        count += 1

        length = get_uint32_big_array(size)
        payload = f.read(size)

        print('write count: ' + str(count))
        flash_data(length, payload)
    f.close()

    flash_end(file_crc,run_addr)

def send_file2sdcard(file_name, target_name, run_addr):
    f = open(file_name, 'rb')
    file_length = os.path.getsize(file_name)
    bytes_left = file_length
    max_length = 65536
    file_crc = crc32(f.read(file_length))

    sdcard_begin(file_length, target_name)

    f.seek(0, 0)
    count = 0
    while bytes_left > 0:
        if bytes_left > max_length:
            size = max_length
        else:
            size = bytes_left
        bytes_left -= size
        count += 1

        length = get_uint32_big_array(size)
        payload = f.read(size)

        print('write count: ' + str(count))
        sdcard_data(length, payload)
    f.close()

    sdcard_end(file_crc,run_addr)

def get_boot_version(port):
    send_request(port, version_tag)
    response = wait_response(port)

    if not response_verify(response, version_tag):
        log.die('failed to get ROM version!')

    payload = response_get_payload(response)
    version = payload.decode('UTF-8')
    log.inf('ROM version: ' + version)



def change_host_baud(port, new_baud):
    port.baudrate = new_baud
    time.sleep(0.01)
    port.reset_output_buffer()
    port.reset_input_buffer()


def sync_baud(port, new_baud):
    payload = get_uint32_big_array(new_baud)

    time.sleep(0.01)
    port.reset_output_buffer()
    port.reset_input_buffer()
    send_request(port, baud_tag, payload)
    response = wait_response(port)
    if not response_verify(response, baud_tag):
        log.dir('modify baudrate to ' + new_baud + ' failed!')
    port.baudrate = new_baud
    time.sleep(0.01)
    port.reset_output_buffer()
    port.reset_input_buffer()



def execute(port, address):
    payload = get_uint32_big_array(address)

    send_request(port, execute_tag, payload)
    response = wait_response(port)
    if not response_verify(response, execute_tag):
        log.die('excute at ' + address + ' failed!') 

def reboot(address):
    length = get_uint32_big_array(4)
    payload = get_uint32_big_array(address)

    send_request(port, reboot_tag, length, payload)
    response = wait_response(port)
    if not response_check_success(response, reboot_tag):
        exit(1)



























SERIAL_DEVICE_NAME = 'USB Single Serial'
# SERIAL_DEVICE_NAME = 'FT232R'
# SERIAL_DEVICE_NAME = 'CP2102N'


SERIAL_DEVICE_PORT = None



def test():
    global SERIAL_DEVICE_PORT

    SERIAL_DEVICE_PORT = init_serial_device(SERIAL_DEVICE_NAME)

    reset_to_download(SERIAL_DEVICE_PORT)
    sync(SERIAL_DEVICE_PORT)
    get_boot_version(SERIAL_DEVICE_PORT)

    sync_baud(SERIAL_DEVICE_PORT, 1000000)
    sync(SERIAL_DEVICE_PORT)

    send_file2mem(SERIAL_DEVICE_PORT, '/home/andy/Documents/recovery/build/zephyr/zephyr.bin', 0x20200000)
    execute(SERIAL_DEVICE_PORT, 0x20200000)

    change_host_baud(SERIAL_DEVICE_PORT, 3000000)
    sync(SERIAL_DEVICE_PORT)






test()