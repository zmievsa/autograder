from pathlib import Path
from canvasapi import Canvas
from .auth import Token, FILE_WITH_TOKEN_INFO

import shutil


def upload_results(results_dir: Path, course_id: int, assignment_id: int, grade: bool):
    # TODO
    print(f"Upload({results_dir}, {course_id}, {assignment_id}, {grade})")
    raise NotImplementedError
    shutil.make_archive(str(results_dir.with_suffix(".zip")), "zip", results_dir)
    token = Token.from_file(FILE_WITH_TOKEN_INFO)
    api = Canvas(token.base_url, token.token)
    submissions = api.get_course(course_id).get_assignment(assignment_id).get_submissions()
