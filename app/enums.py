import enum


class Provider(str, enum.Enum):
    GITHUB = "github"
    GITLAB = "gitlab"
