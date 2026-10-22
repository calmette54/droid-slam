"""Greeter library: personalized greetings in several languages.

Example:
    >>> from greeter import Greeter, LanguageCode
    >>> Greeter("Alice").greet(LanguageCode.FR)
    'Bonjour, Alice!'
"""

from enum import Enum


class LanguageCode(Enum):
    """Languages supported by Greeter."""

    EN = "en"  #: English
    DE = "de"  #: German (Deutsch)
    ES = "es"  #: Spanish (Español)
    FR = "fr"  #: French (Français)


_GREETINGS = {
    LanguageCode.EN: "Hello, {}!",
    LanguageCode.DE: "Hallo, {}!",
    LanguageCode.ES: "¡Hola, {}!",
    LanguageCode.FR: "Bonjour, {}!",
}


class Greeter:
    """Says hello to one person in multiple languages."""

    def __init__(self, name: str) -> None:
        """Stores the name to greet.

        Raises:
            ValueError: if the name is empty.
        """
        if not name:
            raise ValueError("Greeter: name must not be empty")
        self.name = name

    def greet(self, lang: LanguageCode = LanguageCode.EN) -> str:
        """Returns the greeting for the stored name in the given language."""
        return _GREETINGS[lang].format(self.name)
