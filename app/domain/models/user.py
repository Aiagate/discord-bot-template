from dataclasses import dataclass


@dataclass
class User:
    id: int
    name: str
    email: str

    def change_email(self, new_email: str) -> "User":
        """メールアドレスを変更するドメインロジック"""
        self.email = new_email

        return self
