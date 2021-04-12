# Miscellaneous functions used in several modules
#
# :copyright:
#    ETH Zurich, Switzerland
# :license:
#    GNU Lesser General Public License, Version 3
#    (https://www.gnu.org/copyleft/lesser.html)
#


import os
import re
import subprocess
import sys
import time
import typing

from obspy import UTCDateTime


def stream_copy(stream_src):
    # adjustments because of bug in obspy Stats.copy
    stream = stream_src.copy()
    for idx in range(len(stream)):
        stream[idx].stats.sampling_rate = stream_src[idx].stats.sampling_rate
    return stream


def filename_to_int(filename, start_time):
    '''
    Integer with as many digits as start_time

    Example for filename: 2017-02-09T13-24-50-225998Z_Grimsel.h5
    The first 26 characters describe the time.
    '''
    s = ''.join(re.findall(r'\d+', filename[:26]))
    start_int = int(re.sub(r'[^\d]', '', str(start_time)))
    diff = len(str(start_int)) - len(s)
    if diff > 0:
        s += '0' * diff
    return int(s[0:len(str(start_time))])


def file_of_time(asdf_folder, start_time, file_length):
    start_int = int(re.sub(r'[^\d]', '', str(start_time)))

    # find last file with time before start_time
    file = [f for f in sorted(os.listdir(asdf_folder)) if f.endswith('.h5')
        and filename_to_int(f, start_time) <= start_int][-1]

    # check if start_time is in file time
    diff = (UTCDateTime(timestr_to_UTCDateTime(file[:-3])) + file_length
        - UTCDateTime(timestr_to_UTCDateTime(start_time)))
    if diff < 0:
        return None
    return file


def utc_format(utc, fmt):
    if fmt == 'human_time':
        f = utc.strftime('%f')
        return utc.strftime('%H:%M:%S.') + f[:3] + '\'' + f[3:]
    elif fmt == 'filename':
        # shorten to 4 decimal places
        return utc.strftime('%Y%m%d_%H%M%S_%f')[:-2]
    elif fmt == 'key':
        # display in event list of GUI
        f = utc.strftime('%f')
        return utc.strftime('%Y-%m-%d  %H:%M:%S.') + f[:3] + '\'' + f[3:]


def timestr_to_UTCDateTime(timestr):
    '''
    Takes strings with arbitrary delimiters

    order must be: YYYY dd mm HH SS frac
    year must have 4 digits
    all other parts must have 2 digits, except fractions of seconds
    '''
    s = ''.join(re.findall(r'\d+', timestr))
    p = [s[i:i + 2] for i in range(0, len(s), 2)]
    result = f'{p[0]}{p[1]}-{p[2]}-{p[3]}'
    if (len(p) > 4):
        result += f'T{p[4]}'
    if (len(p) > 5):
        result += f':{p[5]}'
    if (len(p) > 6):
        result += f':{p[6]}'
    if (len(p) > 7):
        result += f'.{"".join(p[7:])}'
    return UTCDateTime(result)


def redis_server_start(dir):
    os.system('pkill -9 -f "redis-server"')
    file = os.path.join(dir, 'redis.log')
    with open(file, 'w') as fh:
        fh.write('')
    cmd = [
        'redis-server',
        '--logfile',
        file,
        '--daemonize',
        'yes',
    ]
    if sys.platform == 'win32':
        cmd.insert(0, 'start')
    subprocess.run(cmd)

    # This is necessary because it takes some time until the server is ready.
    t0 = time.time()
    timeout = 1
    while not redis_server_check():
        if time.time() - t0 > timeout:
            return f'Unable to start Redis, timeout after {timeout} sec.'
    return ''


def redis_server_check():
    import redis  # NOQA
    r = redis.Redis()
    try:
        r.set('test', 'test')
    except:
        return False
    else:
        return True


def redis_set_ac_continue(value):
    import redis  # NOQA
    r = redis.Redis()
    try:
        r.set('ac_continue', value)
    except:
        return False
    else:
        return True


def redis_get_ac_continue():
    import redis  # NOQA
    r = redis.Redis()
    if not redis_server_check():
        return False

    result = r.get('ac_continue')
    if result is not None and result.decode('utf-8') == 'yes':
        return True
    return False


def pretty_filesize(num: typing.Union[int, float]) -> str:
    """
    Handy formatting for human readable filesizes.

    From http://stackoverflow.com/a/1094933/1657047

    Args:
        num: The filesize in bytes.
    """
    for x in ["bytes", "KB", "MB", "GB"]:
        if num < 1024.0 and num > -1024.0:
            return "%3.1f %s" % (num, x)
        num /= 1024.0
    return "%3.1f %s" % (num, "TB")