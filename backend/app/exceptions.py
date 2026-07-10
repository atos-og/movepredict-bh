class AppError(Exception):
    status_code = 500
    code = "application_error"

    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details


class ResourceNotFoundError(AppError):
    status_code = 404
    code = "resource_not_found"


class DataSourceUnavailableError(AppError):
    status_code = 503
    code = "data_source_unavailable"
