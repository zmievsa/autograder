import re
from pathlib import Path
from typing import Dict, Any

from .exit_codes import ExitCodeEventType
from .testcase_result_validator import LAST_LINE_SPLITTING_CHARACTER

template_matcher = re.compile("{ *% *([A-Za-z0-9_]+) *% *}")

FORMAT_KWARGS = {
    "RESULT_EXIT_CODE": str(int(ExitCodeEventType.RESULT)),
    "CHECK_STDOUT_EXIT_CODE": str(int(ExitCodeEventType.CHECK_STDOUT)),
    "CHEAT_ATTEMPT_EXIT_CODE": str(int(ExitCodeEventType.CHEAT_ATTEMPT)),
    "SPLITCHAR": LAST_LINE_SPLITTING_CHARACTER,
}


def format_template(template: str, safe=True, **kwargs: Dict[str, Any]):
    # We use dict here to filter repeated matches
    matches = {m.group(1): m.group(0) for m in template_matcher.finditer(template)}
    for attr, matched_string in matches.items():
        value = kwargs.pop(attr, None)
        if value is None:
            raise ValueError(f"Attribute '{attr}' not supplied")
        template = template.replace(matched_string, str(value))
    if len(kwargs) and safe:
        raise ValueError("Too many arguments supplied: " + ", ".join(kwargs.keys()))
    return template


def get_formatted_test_helper(path_to_test_helper: Path) -> str:
    with path_to_test_helper.open() as helper_file:
        return format_template(helper_file.read(), safe=False, **FORMAT_KWARGS)
