"""Security Passport — evidence-backed operational passport for
European financial instruments."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("security-passport")
except PackageNotFoundError:
    __version__ = "0+unknown"


def user_agent() -> str:
    """Single canonical outbound User-Agent for every provider."""
    return f"security-passport/{__version__}"
