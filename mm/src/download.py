import json, shutil
from pathlib import Path
import util, log, mmp

DARWIN_MOUNT_PATH = None

def darwin_recursive_parsing(data, vid, pid):
    global DARWIN_MOUNT_PATH

    if DARWIN_MOUNT_PATH is not None:
        return

    if isinstance(data, list):
        for list_item in data:
            darwin_recursive_parsing(list_item, vid, pid)
    elif isinstance(data, dict):
        vender_id = data.get('vendor_id')
        product_id = data.get('product_id')
        if vender_id is not None and product_id is not None:
            vender_id = vender_id.lower()
            product_id = product_id.lower()
            if vender_id.startswith(vid) and product_id.startswith(pid):
                first = data.get('Media')
                if first is not None:
                    second = first[0].get('volumes')
                    if second is not None:
                        third = second[0].get('mount_point')
                        if third is not None:
                            #DARWIN_MOUNT_PATH = data.get('Media')[0].get('volumes')[0].get('mount_point')
                            DARWIN_MOUNT_PATH = third
                            return
        for key, value in data.items():
            if isinstance(value, dict):
                darwin_recursive_parsing(value, vid, pid)
            elif isinstance(value, list):
                for list_item in value:
                    darwin_recursive_parsing(list_item, vid, pid)

def darwin_get_mount_point():
    vid = mmp.get_board_info('vid')
    pid = mmp.get_board_info('pid')

    flags = [
        'system_profiler',
        '-json SPUSBDataType'
    ]
    json_data = util.run_command(flags)
    parsed = json.loads(json_data)

    DARWIN_MOUNT_PATH = None
    darwin_recursive_parsing(data=parsed, vid=vid, pid=pid)

    return DARWIN_MOUNT_PATH


def darwin_eject():
    flags = [
        'diskutil',
        'eject',
        util.quote_string(DARWIN_MOUNT_PATH)
    ]
    log.inf('Ejecting SD card...')

    if util.command(flags):
        log.die('eject SD card failed!')


def darwin_download(source):
    log.inf('Detecting SD card...')
    darwin_get_mount_point()

    if DARWIN_MOUNT_PATH is None:
        board_name = mmp.get_board_name()
        log.die('Cannot find ' + board_name + ', please make sure it is successfully mounted')

    log.inf(DARWIN_MOUNT_PATH + ' found')
    file_name = source.name

    target = Path(DARWIN_MOUNT_PATH) / file_name
    log.inf('Copying ' + file_name + '...')
    shutil.copyfile(source, target)
    darwin_eject()
