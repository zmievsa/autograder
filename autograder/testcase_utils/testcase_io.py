from pathlib import Path
from typing import Callable, Dict

from ..config_manager import DEFAULT_ARGLIST_VALUE_KEY

FORMATTER_TYPE = Callable[[str], str]


class TestCaseIO:
    """Represents everything related to stdin/stdout in testcase_utils"""

    stem: str
    formatter: FORMATTER_TYPE

    def __init__(
        self,
        testcase_path: Path,  # A path of either input or output
        formatters: Dict[str, FORMATTER_TYPE],
        input_dir: Path,
        output_dir: Path,
    ):
        self.name = testcase_path.name
        self.stem = testcase_path.stem
        f = formatters  # to make next line shorter
        self.formatter = f.get(self.stem) or f.get(DEFAULT_ARGLIST_VALUE_KEY) or default_formatter
        self.output_file: Path = output_dir / f"{self.stem}.txt"

        if self.output_file.exists() and self.output_file.is_file():
            self.expected_output_backup = self.output_file.read_text()
            self.expected_output = self.format_output(self.expected_output_backup)
            self.output_file.write_text("")
        else:
            self.expected_output_backup = ""
            self.expected_output = ""

        input_file: Path = input_dir / f"{self.stem}.txt"
        if input_file.exists() and input_file.is_file():
            self.input = input_file.read_text().strip()
        else:
            self.input = ""

    def format_output(self, output: str) -> str:
        # Replacement of \r\n accounts for inconsistent line endings between systems
        return self.formatter(output).replace("\r\n", "\n")

    def expected_output_equals(self, output: str) -> bool:
        return self.format_output(output) == self.expected_output

    @classmethod
    def get_empty_io(cls):
        io = cls(Path("nonexistent"), {}, Path(), Path())
        io.expected_output = ""
        io.input = ""
        return io

    def cleanup(self):
        if self.output_file.exists() and self.output_file.is_file():
            self.output_file.write_text(self.expected_output_backup)


def default_formatter(s: str) -> str:
    return s
