import subprocess
from subprocess import check_output
import shlex
from config import config


def script_check(source, language, input, output, max_time):
    langdict = {
        'python':'PYTHON_INTERPRETER_PATH'
    }

    path = config[langdict[language]]
    args = path + ' ' + source + ' ' + input
    try:
        sout = check_output(shlex.split(args), stderr=subprocess.STDOUT, timeout=max_time, shell=True)
    except subprocess.TimeoutExpired:
        return 'Timeout', 'Истекло время выполнения теста!'
    if sout == output:
        return 'Completed'
    else:
        return 'Failed', sout