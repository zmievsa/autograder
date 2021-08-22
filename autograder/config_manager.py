import configparser
from pathlib import Path
from typing import Any, Callable, Dict, List, TypeVar

from .testcase_utils.abstract_testcase import ArgList

DEFAULT_FILE_STEM = "Homework"


class GradingConfig:
    timeouts: Dict[str, float]
    generate_results: bool
    parallel_grading_enabled: bool
    stdout_only_grading_enabled: bool
    total_points_possible: int
    total_score_to_100_ratio: float

    assignment_name: str
    any_submission_file_name_is_allowed: bool
    possible_source_file_stems: List[str]
    testcase_weights: Dict[str, float]
    cli_argument_lists: Dict[ArgList, Dict[str, List[str]]]

    def __init__(self, config: Path, default_config: Path):
        self._configure_grading(config, default_config)

    def _configure_grading(
        self,
        config_path: Path,
        default_config_path: Path,
    ):
        cfg = self._read_config(config_path, default_config_path)

        self.timeouts = parse_config_list(cfg["TIMEOUT"], float)
        self.generate_results = cfg.getboolean("GENERATE_RESULTS")
        self.parallel_grading_enabled = cfg.getboolean("PARALLEL_GRADING_ENABLED")
        self.stdout_only_grading_enabled = cfg.getboolean("STDOUT_ONLY_GRADING_ENABLED")

        self.total_points_possible = cfg.getint("TOTAL_POINTS_POSSIBLE")
        self.total_score_to_100_ratio = self.total_points_possible / 100

        self.assignment_name = cfg["ASSIGNMENT_NAME"]

        source = cfg["POSSIBLE_SOURCE_FILE_STEMS"].strip()
        if source == "AUTO":
            source = DEFAULT_FILE_STEM
            self.any_submission_file_name_is_allowed = True
        else:
            self.any_submission_file_name_is_allowed = False
        self.possible_source_file_stems = source.replace(" ", "").split(",")

        self.testcase_weights = parse_config_list(cfg["TESTCASE_WEIGHTS"], float)

        # TODO: Name me better. The name is seriously bad
        self.cli_argument_lists = parse_arglists(cfg)

    @staticmethod
    def _read_config(path_to_user_config: Path, path_to_default_config: Path) -> configparser.SectionProxy:
        default_parser = configparser.ConfigParser()
        default_parser.read(str(path_to_default_config))

        user_parser = configparser.ConfigParser()
        user_parser.read_dict(default_parser)
        user_parser.read(str(path_to_user_config))

        return user_parser["CONFIG"]

    def generate_arglists(self, file_name: str) -> Dict[ArgList, List[str]]:
        arglist = {}
        for arglist_index, arglists_per_file in self.cli_argument_lists.items():
            if file_name in arglists_per_file:
                arglist[arglist_index] = arglists_per_file[file_name]
            elif "ALL" in arglists_per_file:
                arglist[arglist_index] = arglists_per_file["ALL"]
            else:
                arglist[arglist_index] = tuple()
        return arglist


T = TypeVar("T")


def parse_config_list(config_line: str, value_type: Callable[[Any], T]) -> Dict[str, T]:
    """Reads in a config line in the format: 'file_name:value, file_name:value, ALL:value'
    ALL sets the default value for all other entries
    """
    config_entries = {}
    for config_entry in config_line.split(","):
        if config_entry.strip():
            testcase_name, value = config_entry.strip().split(":")
            config_entries[testcase_name.strip()] = value_type(value)
    return config_entries


def parse_arglists(cfg: configparser.SectionProxy) -> Dict[ArgList, Dict[str, List[str]]]:
    argument_lists = {n: {} for n in ArgList}
    for arg_list_enum in ArgList:
        arg_list = parse_config_list(cfg[arg_list_enum.value], convert_to_arglist)
        for testcase_name, args in arg_list.items():
            argument_lists[arg_list_enum][testcase_name] = args
    return argument_lists


def convert_to_arglist(s: str) -> List[str]:
    return str(s).replace("  ", " ").strip().split()
