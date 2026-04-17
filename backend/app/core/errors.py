"""Custom exception classes for Solarware application."""


class SolarwareError(Exception):
    """Base exception for all Solarware errors."""

    def __init__(self, message: str, code: int = 500):
        self.message = message
        self.code = code
        super().__init__(self.message)


class ValidationError(SolarwareError):
    """Raised when input validation fails."""

    def __init__(self, message: str):
        super().__init__(message, code=400)


class GeocodingError(SolarwareError):
    """Raised when geocoding operations fail."""

    def __init__(self, message: str):
        super().__init__(message, code=400)


class SatelliteDataError(SolarwareError):
    """Raised when satellite data retrieval fails."""

    def __init__(self, message: str):
        super().__init__(message, code=502)


class BuildingDetectionError(SolarwareError):
    """Raised when building detection fails."""

    def __init__(self, message: str):
        super().__init__(message, code=500)


class ContactEnrichmentError(SolarwareError):
    """Raised when contact enrichment fails."""

    def __init__(self, message: str):
        super().__init__(message, code=500)


class VisualizationError(SolarwareError):
    """Raised when visualization generation fails."""

    def __init__(self, message: str):
        super().__init__(message, code=500)


class MailingPackError(SolarwareError):
    """Raised when mailing pack generation fails."""

    def __init__(self, message: str):
        super().__init__(message, code=500)


class EmailError(SolarwareError):
    """Raised when email operations fail."""

    def __init__(self, message: str):
        super().__init__(message, code=500)


class NotFoundError(SolarwareError):
    """Raised when requested resource is not found."""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, code=404)


class RateLimitError(SolarwareError):
    """Raised when API rate limit is exceeded."""

    def __init__(self, message: str, retry_after: int = 60):
        super().__init__(message, code=429)
        self.retry_after = retry_after
