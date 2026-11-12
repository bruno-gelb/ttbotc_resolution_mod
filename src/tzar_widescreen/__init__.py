"""Widescreen mod for Tzar: The Burden of the Crown."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("ttbotc-resolution-mod")
except PackageNotFoundError:  # running from a source tree that isn't installed
    __version__ = "unknown"
