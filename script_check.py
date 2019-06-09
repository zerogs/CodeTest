import subprocess
import shlex
from config import config


def script_check(source, language, input, output):
    langdict = {
        'python':'PYTHON_INTERPRETER_PATH'
    }

    path = config[langdict[language]]
    args = path + ' ' + source + ' ' + input
    process = subprocess.Popen(shlex.split(args), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    data = process.communicate()[0].decode('utf-8')[:-1]
    process.kill()
    if data == output:
        return 'Completed'
    else:
        return 'Failed', data