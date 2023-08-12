import os
import threading

from app.src.constants import voice_alert_frequency


def _run_os_system(command, repeat):
    for _ in range(repeat):
        os.system(command)


def voice_alert(msg, repeat=voice_alert_frequency):
    thread = threading.Thread(target=_run_os_system, args=(msg, repeat))
    thread.start()
    thread.join()


# voice_alert('say task completed', 5)
