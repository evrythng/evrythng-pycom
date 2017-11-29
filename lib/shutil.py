import os


def rmtree(top):
    dir_flag = 0x4000
    for name in os.listdir(top):
        path = top + os.sep + name
        if os.stat(path)[0] & dir_flag == dir_flag:
            rmtree(path)
        else:
            os.unlink(path)
    os.rmdir(top)


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
    else:
        while True:
            buf = src.read(length)
            if not buf:
                break
            dest.write(buf)
