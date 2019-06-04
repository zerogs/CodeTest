import subprocess
import docker
import shlex
from config import config


def script_check(source, language, input, output):
    langdict = {
        'python':'PYTHON_INTERPRETER_PATH'
    }

    path = config[langdict[language]]
    args = path + ' ' + source + ' ' + input
    #p = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
    #data = p.communicate()[0]
    #p.kill()
    process = subprocess.Popen(shlex.split(args), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    data = process.communicate()[0].decode('utf-8')[:-1]
    process.kill()
    if data == output:
        return 'Completed', data
    else:
        return 'Failed', data