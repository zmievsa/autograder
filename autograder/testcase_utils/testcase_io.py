from contextlib import contextmanager
from io import StringIO
from pathlib import Path


class TestCaseIO:
    """Represents everything related to stdin/stdout in testcase_utils"""

    def __init__(self, testcase_name_stem, formatters, input_dir, output_dir):
        self.name = testcase_name_stem
        self.formatter = formatters.get(self.name, None) or formatters.get("ALL", None)
        self.output_file: Path = output_dir / f"{self.name}.txt"

        if self.output_file.exists() and self.output_file.is_file():
            with self.output_file.open() as f:
                self.expected_output_backup = f.read()
                self.expected_output = self.format_output(self.expected_output_backup)
            with self.output_file.open("w") as f:
                f.write("")
        else:
            self.expected_output_backup = ""
            self.expected_output = ""

        input_file: Path = input_dir / f"{self.name}.txt"
        if input_file.exists() and input_file.is_file():
            with input_file.open() as f:
                self._input = StringIO(f.read().strip())
        else:
            self._input = StringIO("")

    def format_output(self, output: str) -> str:
        return output if self.formatter is None else self.formatter(output)

    @contextmanager
    def input(self):
        try:
            yield self._input
        finally:
            self._input.seek(0)

    def expected_output_equals(self, output: str) -> bool:
        return self.format_output(output) == self.expected_output

    @classmethod
    def get_empty_io(cls):
        io = TestCaseIO("/*", {}, Path(), Path())
        io.expected_output = ""
        io._input = StringIO("")
        return io

    def cleanup(self):
        if self.output_file.exists() and self.output_file.is_file():
            with self.output_file.open("w") as f:
                f.write(self.expected_output_backup)
