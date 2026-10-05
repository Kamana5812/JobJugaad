"""One shared subprocess slot per API process; no distributed capacity claim."""
from threading import BoundedSemaphore

PARSER_SLOTS = BoundedSemaphore(1)
