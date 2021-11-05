from tomlkit.api import parse, dumps
from pathlib import Path


doc = parse(Path("autograder/default_config.ini").read_text())

doc2 = parse(Path("examples/c/tests/config.ini").read_text())


print(dumps(doc2))
