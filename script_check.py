import os, glob, subprocess
from config import config


def script_check(source, language, input, output):
    langdict = {
        'python':'PYTHON_INTERPRETER_PATH',
        'cpp' : 'GCC_COMPILER_PATH'
    }

    path = config[langdict[language]]
    args = path + ' ' + source + ' ' + input
    p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    data = p.communicate()
    data = data[0].decode('utf-8')[:-2]
    p.kill()
    if data == output:
        print('Completed!')
        print(data)
        return 'Completed', data
    else:
        print('Failed!')
        print(data)
        return 'Failed', data