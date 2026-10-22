"""Command-line front end for the greeter library.

Usage: `hello-world [name] [en|de|es|fr]`. Prints a greeting for `name`
(default "world") in the given language (default English).
"""

import sys

from greeter import Greeter, LanguageCode


def main(argv: list[str]) -> int:
    """Prints the greeting; returns 0 on success, 1 on invalid arguments."""
    try:
        name = argv[1] if len(argv) > 1 else "world"
        try:
            lang = LanguageCode(argv[2]) if len(argv) > 2 else LanguageCode.EN
        except ValueError:
            raise ValueError(f"unsupported language: {argv[2]}") from None
        print(Greeter(name).greet(lang))
        return 0
    except ValueError as e:
        print(f"error: {e}\nusage: {argv[0]} [name] [en|de|es|fr]", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
