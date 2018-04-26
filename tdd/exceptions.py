class UserError(ValueError):
    """Raise whenever user makes a mistake (config) or malformed input data"""

class TDDConfigError(UserError):
    """Wrong config"""

class TDDInternalError(Exception):
    """Raise when I made a mistake"""
