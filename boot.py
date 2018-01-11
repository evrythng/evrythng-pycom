import os
import shutil
import machine
import led

uart = machine.UART(0, 115200)
os.dupterm(uart)

led.off()

try:
    # check if upgrade did not finish successfully
    os.stat(shutil.upgrade_in_progress_flag_path)
except Exception:
    pass
else:
    print('incomplete upgrade detected, restoring previous firmware...')
    shutil.copy_fw_files(shutil.previous_fw_dir, shutil.current_fw_dir)
    print('done, rebooting...')
    os.unlink(shutil.upgrade_in_progress_flag_path)
    machine.reset()
