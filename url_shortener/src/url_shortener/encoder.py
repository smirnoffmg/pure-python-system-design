import string
from abc import ABC, abstractmethod


class BaseEncoder(ABC):
    @abstractmethod
    def encode(self, n: int) -> str: ...

    @abstractmethod
    def decode(self, s: str) -> int: ...


class Base62Encoder(BaseEncoder):
    ALPHABET = string.digits + string.ascii_letters
    BASE = len(ALPHABET)

    def encode(self, n: int) -> str:
        """
        Encode an integer to its Base62 string representation.

        Args:
            n (int): The non-negative integer to be encoded.

        Returns:
            str: The Base62 encoded string.

        Raises:
            ValueError: If the input is a negative integer.
        """
        if n < 0:
            raise ValueError("Base62 encoding does not support negative numbers.")

        if n == 0:
            return self.ALPHABET[0]

        res = []

        while n > 0:
            n, r = divmod(n, self.BASE)
            res.append(self.ALPHABET[r])

        return "".join(reversed(res))

    def decode(self, s: str) -> int:
        """
        Decode a Base62 string back to an integer.

        Args:
            s (str): Base62 encoded string.

        Returns:
            int: The decoded integer.

        Raises:
            ValueError: If `s` contains invalid characters.
        """
        if not s:
            raise ValueError("Input string is empty")

        num = 0
        for char in s:
            value = self.ALPHABET.index(char)
            num = num * self.BASE + value

        return num
