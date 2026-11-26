"""Bound untrusted URL integers before dispatching API views."""

MAX_BIGINT = 2**63 - 1


class BoundedIntegerConverter:
    # PostgreSQL BigAutoField uses signed 64-bit integers. Keep zero for
    # zero-based ticket indices; object-specific validation remains in views.
    regex = r"[0-9]{1,19}"

    def to_python(self, value):
        number = int(value)
        if not 0 <= number <= MAX_BIGINT:
            raise ValueError("Integer outside supported range")
        return number

    def to_url(self, value):
        text = str(value)
        if not text.isascii() or not text.isdecimal() or len(text) > 19:
            raise ValueError("Integer outside supported range")
        self.to_python(text)
        return text
