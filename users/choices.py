from enum import Enum


class UserType(str, Enum):
    ADMIN = "ADMIN"
    REGULAR = "REGULAR"


class LeaveType(str, Enum):
    SICK_LEAVE = "SICK_LEAVE"
    PRIVILEGE_LEAVE = "PRIVILEGE_LEAVE"
