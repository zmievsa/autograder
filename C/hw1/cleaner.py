# TODO: Remove all submissions but the last one

from pathlib import Path

line_requirements = {
    "main": ["int main", "void main"],
}

def is_main_line(line):
    return any(req in line for req in line_requirements['main'])

def clean_line(line):
    return " ".join(line.split())  # removes all duplicating whitespace

def edit_submission(submission):
    with submission.open(errors="replace") as f:
        lines = [clean_line(l) for l in f.readlines()]
        currently_iterating_main = False
        main_start_index = 0
        main_end_index = 0
        braces = 0
        for i in range(len(lines)):
            if "printf" in lines[i] or "scanf" in lines[i]:
                lines[i] = "// " + lines[i]
                continue
            if "{" in lines[i]:
                braces += 1
            if "}" in lines[i]:
                braces -= 1
            if is_main_line(lines[i]):
                currently_iterating_main = True
                main_start_index = i
            elif currently_iterating_main and braces == 0:
                currently_iterating_main = False
                main_end_index = i
        if (main_end_index < main_start_index):
            print(f"Failed to find main even though there is one: {submission}, {main_start_index}:{main_end_index}")
        else:
            lines = lines[:main_start_index] + lines[main_end_index+1:]

    with submission.open("w") as f:
        f.write("\n".join(lines))


submissions = Path("submissions/")
for submission in submissions.iterdir():
    try:
        edit_submission(submission)
    except Exception as e:
        print(submission)
        raise e
# edit_submission(Path("wojer.c"))