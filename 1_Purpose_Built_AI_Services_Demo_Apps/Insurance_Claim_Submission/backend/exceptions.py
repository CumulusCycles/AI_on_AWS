"""
Custom exceptions for the AWS AI Services Demo API.
"""


class AWSServiceError(Exception):
    """Base exception for AWS service errors."""
    pass


class TextractError(AWSServiceError):
    """Exception raised when Textract service encounters an error."""
    pass


class ComprehendError(AWSServiceError):
    """Exception raised when Comprehend service encounters an error."""
    pass


class RekognitionError(AWSServiceError):
    """Exception raised when Rekognition service encounters an error."""
    pass


class TranslateError(AWSServiceError):
    """Exception raised when Translate service encounters an error."""
    pass


class PollyError(AWSServiceError):
    """Exception raised when Polly service encounters an error."""
    pass

