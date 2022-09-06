
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from io import StringIO


@contextmanager
def silence_output():
    with StringIO() as buf, redirect_stdout(buf), redirect_stderr(buf):
        yield buf

