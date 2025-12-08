from enum import StrEnum


class CurrencyEnum(StrEnum):
    """Enumeration of supported currencies."""
    USD = "USD"
    EUR = "EUR"
    AUD = "AUD"
    CAD = "CAD"
    ARS = "ARS"
    PLN = "PLN"
    BTC = "BTC"
    ETH = "ETH"
    DOGE = "DOGE"
    USDT = "USDT"


class UserStatusEnum(StrEnum):
    """Enumeration of user statuses."""

    ACTIVE = "ACTIVE"
    BLOCKED = "BLOCKED"


class TransactionStatusEnum(StrEnum):
    """Enumeration of transaction statuses."""

    PROCESSED = "PROCESSED"
    ROLLBACKED = "ROLLBACKED"


class TransactionTypeEnum(StrEnum):
    """Enumeration of transaction types."""

    DEPOSIT = "DEPOSIT"
    WITHDRAW = "WITHDRAW"
