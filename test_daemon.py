import threading
from script_check import script_check
from pony.orm import db_session, select, ObjectNotFound
from models import Result, Attempt, Test
import time
from queue import Queue

testing_queue = Queue(maxsize=128)

@db_session
def program_testing(attemptid):
    print('Testing...')
    try:
        attempt = Attempt[attemptid]
    except ObjectNotFound:
        return None
    var = attempt.variant
    counter = 0
    tests = select(t for t in Test if t.variant == var)
    if len(tests) == 0:
        return None
    for test in tests:
        counter += 1
        out = script_check(attempt.source, attempt.language, test.input, test.output)
        if out[0] != "Completed":
            r = Result(
                tests=var.tests,
                result=False,
                attempt=attempt,
                error=out[1],
                completed_tests=counter,
                failed_id=test.id
            )
            return 0

    r = Result(
        tests=var.tests,
        result=True,
        attempt=attempt
    )

    return 0


def tester():
    print('Worker call...')
    while True:
        attempt = testing_queue.get()
        time.sleep(1)
        if attempt is None:
            break
        test = program_testing(attempt.id)
        if test is None:
            continue
        elif test == 0:
            testing_queue.task_done()


def daemon_start():
    t = threading.Thread(target=tester,
                         name="Tester",
                         args=(),
                         daemon=True)
    t.start()


