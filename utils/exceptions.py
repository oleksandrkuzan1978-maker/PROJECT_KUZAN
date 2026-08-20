"""Пользовательские исключения приложения."""


class ServiceUnavailableError(Exception):
    """Возникает, когда внешний сервис приложения недоступен."""

    def __init__(self, service: str) -> None:
        self.service = service
        super().__init__(f"Service {service} is unavailable.")