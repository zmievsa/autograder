from pathlib import Path
import sys
import re
import sh


RESULT_REGEX = re.compile(r"Result: (\d+)\/\d+")
template_matcher = re.compile("{% *([A-Za-z0-9_]+) *%}")


def format_template(template, **kwargs):
    for match in template_matcher.finditer(template):
        attr = match.group(1)
        value = kwargs.pop(attr, None)
        if value is None:
            raise ValueError(f"Attribute {attr} not supplied")
        template = template.replace(match.group(0), str(value))
    if len(kwargs):
        raise ValueError("Too many arguments supplied: " + ", ".join(kwargs.keys()))
    return template


def get_stderr(current_dir: Path, error: sh.ErrorReturnCode, string):
    error = str(error)
    error_str = string + error[error.find("STDERR:") + len("STDERR"):]
    return error_str.strip().replace(str(current_dir), "...")


def print_results(current_dir, min_score: int, *args, **kwargs):
    with open(current_dir / "grader_output.txt") as f:
        contents = f.read()
    student_outputs = contents.split("\n\n")
    for output in student_outputs:
        match = RESULT_REGEX.search(output)
        if match is not None:
            score = int(match.group(1))
            if score >= min_score:
                print(output + "\n", *args, **kwargs)
