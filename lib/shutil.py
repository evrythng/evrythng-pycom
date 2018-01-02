import os

supported_ext = ('.py', '.json', '.html')
supported_dirs = ['', '/lib', '/www']

upgrade_flag_path = '/flash/.upgrade_me'
upgrade_in_progress_flag_path = '/flash/.upgrade_in_progress'

previous_fw_dir = '/flash/previous.fw'
current_fw_dir = '/flash'


def is_dir(path):
    return os.stat(path)[0] & 0x4000 == 0x4000


def rmtree(top):
    try:
        os.stat(top)
    except OSError:
        return

    for name in os.listdir(top):
        path = top + os.sep + name
        if is_dir(path):
            rmtree(path)
            os.sync()
        else:
            os.unlink(path)
            os.sync()
    os.rmdir(top)
    os.sync()


def copyfileobj(src, dest, length=512):
    if hasattr(src, "readinto"):
        buf = bytearray(length)
        while True:
            sz = src.readinto(buf)
            if not sz:
                break
            if sz == length:
                dest.write(buf)
            else:
                b = memoryview(buf)[:sz]
                dest.write(b)
            os.sync()
    else:
        while True:
            buf = src.read(length)
            if not buf:
                break
            dest.write(buf)
            os.sync()


def create_folders_if_needed(filename):
    # full path should be provided
    folders = filename.split(os.sep)[1:-1]
    next_path = ''
    for f in folders:
        next_path += os.sep + f
        try:
            os.stat(next_path)
        except Exception:
            os.mkdir(next_path)
            os.sync()


def fw_file_list_gen(base_dir):
    for sub_dir in supported_dirs:
        try:
            filenames = os.listdir(base_dir + sub_dir)
        except OSError as e:
            print('failed to list directory (ignored): {}'.format(e))
        else:
            for f in filenames:
                for ext in supported_ext:
                    if f.endswith(ext):
                        yield sub_dir + os.sep + f


def copy_fw_files(src_dir, dst_dir):
    src_filenames = list(fw_file_list_gen(src_dir))
    for f in src_filenames:
        src_filename = src_dir + f
        dst_filename = dst_dir + f
        create_folders_if_needed(dst_filename)
        print('copying {} to {}'.format(src_filename, dst_filename))
        with open(src_filename, 'rb') as src, open(dst_filename, 'wb') as dst:
            copyfileobj(src, dst)
            os.sync()
