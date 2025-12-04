"""API schemas."""
from .auth import (
    UserRegister,
    UserLogin,
    Token,
    TokenData,
    RefreshTokenRequest,
    PasswordChange,
    PasswordReset,
    PasswordResetConfirm,
)
from .user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserDetailResponse,
    UserStats,
    UserPreferences,
)
from .job import (
    JobListItem,
    JobDetailResponse,
    JobListResponse,
    PersonalizedJobsResponse,
    SalaryRange,
    CompanyBrief as JobCompanyBrief,
)
from .company import (
    CompanyCreate,
    CompanyUpdate,
    CompanyResponse,
    CompanyDetailResponse,
    CompanyListItem,
    CompanyListResponse,
    CompanyStats,
)
from .alert import (
    AlertCreate,
    AlertUpdate,
    AlertResponse,
    AlertDetailResponse,
    AlertListResponse,
    AlertTestResponse,
    AlertStats,
)

__all__ = [
    # Auth
    "UserRegister",
    "UserLogin",
    "Token",
    "TokenData",
    "RefreshTokenRequest",
    "PasswordChange",
    "PasswordReset",
    "PasswordResetConfirm",
    # User
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserDetailResponse",
    "UserStats",
    "UserPreferences",
    # Job
    "JobListItem",
    "JobDetailResponse",
    "JobListResponse",
    "PersonalizedJobsResponse",
    "SalaryRange",
    "JobCompanyBrief",
    # Company
    "CompanyCreate",
    "CompanyUpdate",
    "CompanyResponse",
    "CompanyDetailResponse",
    "CompanyListItem",
    "CompanyListResponse",
    "CompanyStats",
    # Alert
    "AlertCreate",
    "AlertUpdate",
    "AlertResponse",
    "AlertDetailResponse",
    "AlertListResponse",
    "AlertTestResponse",
    "AlertStats",
]
