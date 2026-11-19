from fastapi import HTTPException, status


class AppError(HTTPException):
    def __init__(self, status_code: int, detail: str):
        super().__init__(status_code=status_code, detail=detail)


def unauthorized(detail: str = "Could not validate credentials") -> AppError:
    return AppError(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
    )


def forbidden(detail: str = "You do not have access to this resource") -> AppError:
    return AppError(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=detail,
    )


def not_found(detail: str = "Resource not found") -> AppError:
    return AppError(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=detail,
    )


def conflict(detail: str = "Resource already exists") -> AppError:
    return AppError(
        status_code=status.HTTP_409_CONFLICT,
        detail=detail,
    )


def bad_request(detail: str = "Invalid request") -> AppError:
    return AppError(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=detail,
    )


def not_implemented(detail: str) -> AppError:
    return AppError(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail=detail,
    )
