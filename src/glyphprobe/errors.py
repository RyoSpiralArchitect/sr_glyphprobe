class GlyphProbeError(RuntimeError):
    """Base error for user-facing GlyphProbe failures."""


class CapabilityError(GlyphProbeError):
    """Raised when a backend cannot satisfy an experiment contract."""


class ConfigurationError(GlyphProbeError):
    """Raised when a configuration is internally inconsistent."""


class BackendLoadError(GlyphProbeError):
    """Raised when an optional backend dependency or model cannot be loaded."""
