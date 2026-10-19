import logging
import re

# BR-008: never let obvious sensitive values reach logs.
_SENSITIVE = re.compile(r"(password|token|authorization|national_id|id_number)=\S+", re.I)


class RedactFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = _SENSITIVE.sub(r"\1=***", str(record.msg))
        return True


def setup_logging(level: int = logging.INFO) -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    )
    handler.addFilter(RedactFilter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)
