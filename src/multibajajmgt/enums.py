from enum import Enum


class MultiBajajMgtEnum(str, Enum):
    def __str__(self) -> str:
        return str.__str__(self)


class EnvVariable(MultiBajajMgtEnum):
    server_url = "SERVER_URL"
    server_api_key = "SERVER_API_KEY"
    database_name = "DATABASE_NAME"
    server_username = "SERVER_USERNAME"
