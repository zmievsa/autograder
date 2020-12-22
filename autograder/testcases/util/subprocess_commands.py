from pathlib import Path
import subprocess
run(args: _CMD, bufsize: int = ..., executable: str | bytes | _PathLike[str] | _PathLike[bytes] | None = ..., stdin: _FILE = ..., stdout: _FILE = ..., stderr: _FILE = ..., preexec_fn: () -> Any = ..., close_fds: bool = ..., shell: bool = ..., cwd: str | bytes | _PathLike[str] | _PathLike[bytes] | None = ..., env: Mapping[bytes, _TXT] | Mapping[str, _TXT] | None = ..., universal_newlines: bool = ..., startupinfo: Any = ..., creationflags: int = ..., restore_signals: bool = ..., start_new_session: bool = ..., pass_fds: Any = ..., *, capture_output: bool = ..., check: bool = ..., encoding: str | None = ..., errors: str | None = ..., input: str | None = ..., text: Literal[True], timeout: float | None = ...) -> CompletedProcess[str]
subprocess.run
def run(
    *args,
    stdin=None,
    input=None,
    stdout=None,
    stderr=None,
    capture_output=False,
    shell=False,
    cwd=None,
    timeout=None,
    check=False,
    encoding=None,
    errors=None,
    text=None,
    env=None,
    universal_newlines=None,
    OTHER_POPEN_KWARGS,
    bufsize=-1,
    executable: Path=None,
    preexec_fn=None,
    close_fds=True,
    startupinfo=None,
    creationflags=0,
    restore_signals=True,
    start_new_session=False,
    pass_fds=(),
    group=None,
    extra_groups=None,
    user=None,
    umask=-1
):
    pass