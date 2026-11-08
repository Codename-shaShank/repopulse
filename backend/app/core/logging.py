import logging
import sys

_SENSITIVE_KEYS = ("authorization", "token", "password", "secret", "api-key")

_CONFIGURED = False


class RedactingFilter(logging.Filter):
    """Drops anything that looks like a credential before it reaches a handler."""

    def filter(self, record: logging.LogRecord) -> bool:
        message = str(record.getMessage()).lower()
        if any(key in message for key in _SENSITIVE_KEYS):
            record.msg = "[redacted log line containing a credential-like key]"
            record.args = ()
        return True


def configure_logging(level: int = logging.INFO) -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s :: %(message)s")
    )
    handler.addFilter(RedactingFilter())

    root = logging.getLogger()
    root.setLevel(level)
    root.handlers = [handler]
    _CONFIGURED = True
