from enum import Enum


class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"
    SUPERADMIN = "superadmin"


class Language(str, Enum):
    RU = "ru"
    EN = "en"


class Country(str, Enum):
    RUSSIA = "russia"
    USA = "usa"


class ApplicationStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"   