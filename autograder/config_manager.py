import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Generic, List, Mapping, Optional, TypeVar

from tomlkit.api import parse
from tomlkit.container import Container

DEFAULT_FILE_STEM = "Homework"
MAIN_CONFIG_SECTION = "CONFIG"
DEFAULT_ARGLIST_VALUE_KEY = "DEFAULT"


TESTNAME = TypeVar("TESTNAME", bound=str)
VT = TypeVar("VT")


@dataclass
class ArgList(Generic[TESTNAME, VT]):
    mapping: Mapping[TESTNAME, VT]
    fallback_value: VT
    default_value_key: TESTNAME = DEFAULT_ARGLIST_VALUE_KEY  # type: ignore

    def __getitem__(self, key: TESTNAME) -> VT:
        if key in self.mapping:
            return self.mapping[key]
        elif self.default_value_key in self.mapping:
            return self.mapping[self.default_value_key]
        else:
            return self.fallback_value


class GradingConfig:
    file: Mapping[str, Any]

    timeouts: ArgList[str, float]
    generate_results: bool
    generate_student_outputs: bool
    stdout_only_grading_enabled: bool
    total_points_possible: int
    total_score_to_100_ratio: float

    assignment_name: str
    any_submission_file_name_is_allowed: bool
    possible_source_file_stems: List[str]
    testcase_weights: ArgList[str, float]

    def __init__(self, config: Path, default_config: Path):
        self._configure_grading(config, default_config)

    def _configure_grading(
        self,
        config_path: Path,
        default_config_path: Path,
    ):
        global_config = _read_config(config_path, default_config_path)
        self.file = global_config
        cfg = global_config[MAIN_CONFIG_SECTION]
        self.timeouts = ArgList(cfg["TIMEOUT"], 1)
        self.generate_results = cfg["GENERATE_RESULTS"]
        self.generate_student_outputs = cfg["GENERATE_STUDENT_OUTPUTS"]
        self.stdout_only_grading_enabled = cfg["STDOUT_ONLY_GRADING_ENABLED"]

        self.total_points_possible = cfg["TOTAL_POINTS_POSSIBLE"]
        self.total_score_to_100_ratio = self.total_points_possible / 100

        self.assignment_name = cfg["ASSIGNMENT_NAME"]

        self.possible_source_file_stems = cfg["POSSIBLE_SOURCE_FILE_STEMS"]
        if not self.possible_source_file_stems:
            self.possible_source_file_stems = [DEFAULT_FILE_STEM]
            self.any_submission_file_name_is_allowed = True
        else:
            self.any_submission_file_name_is_allowed = False

        self.testcase_weights = ArgList(cfg["TESTCASE_WEIGHT"], 1)

        self.submission_precompilation_args = ArgList(cfg["SUBMISSION_PRECOMPILATION_ARGS"], "")
        self.testcase_precompilation_args = ArgList(cfg["TESTCASE_PRECOMPILATION_ARGS"], "")
        self.testcase_compilation_args = ArgList(cfg["TESTCASE_COMPILATION_ARGS"], "")
        self.testcase_runtime_args = ArgList(cfg["TESTCASE_RUNTIME_ARGS"], "")


def _read_config(config: Path, fallback_config: Optional[Path] = None) -> Mapping[str, Any]:
    if fallback_config is None:
        fallback_doc = None
    else:
        fallback_doc = parse(fallback_config.read_text())
    doc = parse(config.read_text() if config.exists() else "")
    if fallback_doc is not None:
        _config_union(doc, fallback_doc)
    return doc


def _config_union(cfg1: Container, cfg2: Container) -> None:
    """Only works for configs similar to default_config.toml"""
    for k, v in cfg2.items():
        if k not in cfg1:
            cfg1[k] = v
        else:
            for inner_k, inner_v in v.items():
                if inner_k not in cfg1[k]:
                    cfg1[k][inner_k] = inner_v  # type: ignore
