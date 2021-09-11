from pathlib import Path

FILE_WITH_TOKEN_INFO = Path(__file__).parent / "token.txt"


class Token:
    base_url: str
    token: str
    file: Path

    def __init__(self, base_url, token, file_with_token_info: Path):
        self.base_url = base_url.strip()
        self.token = token.strip()
        self.file = file_with_token_info

    @classmethod
    def create(cls, base_url: str, file_with_token_info: Path) -> "Token":
        token = cls(base_url, cls._generate_new_token(base_url), file_with_token_info)
        token.save()
        return token

    @classmethod
    def from_file(cls, file_with_token_info: Path) -> "Token":
        with open(file_with_token_info) as f:
            base_url, token = f
        return cls(base_url, token, file_with_token_info)

    def save(self):
        with open(self.file, "w") as f:
            f.write(f"{self.base_url}\n{self.token}")

    def delete(self):
        self.file.unlink()

    @staticmethod
    def _generate_new_token(base_url: str) -> str:
        # TODO
        raise NotImplementedError
