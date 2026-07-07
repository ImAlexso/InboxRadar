class InboxRadarError(Exception):
    """Base application error."""


class ConfigurationError(InboxRadarError):
    """Raised when local configuration is missing or invalid."""


class AuthenticationError(InboxRadarError):
    """Raised when Microsoft Entra authentication fails."""


class GraphApiError(InboxRadarError):
    """Raised when Microsoft Graph returns an unexpected response."""
