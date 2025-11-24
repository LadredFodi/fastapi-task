from fastapi import HTTPException


class UserAlreadyExistsException(HTTPException):
    """Exception raised when user already exists."""


class UserNotExistsException(HTTPException):
    """Exception raised when user does not exist."""


class UserAlreadyBlockedException(HTTPException):
    """Exception raised when user is already blocked."""


class UserAlreadyActiveException(HTTPException):
    """Exception raised when user is already active."""


class BadRequestDataException(HTTPException):
    """Exception raised for bad request data."""


class NegativeBalanceException(HTTPException):
    """Exception raised when balance would become negative."""


class TransactionNotExistsException(HTTPException):
    """Exception raised when transaction does not exist."""


class TransactionDoesNotBelongToUserException(HTTPException):
    """Exception raised when transaction does not belong to user."""


class CreateTransactionForBlockedUserException(HTTPException):
    """Exception raised when trying to create transaction for blocked user."""


class UpdateTransactionForBlockedUserException(HTTPException):
    """Exception raised when trying to update transaction for blocked user."""


class TransactionAlreadyRollbackedException(HTTPException):
    """Exception raised when transaction is already rollbacked."""
