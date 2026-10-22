import pytest
from greeter import Greeter, LanguageCode


@pytest.mark.parametrize(
    ("lang", "expected"),
    [
        (LanguageCode.EN, "Hello, Tests!"),
        (LanguageCode.DE, "Hallo, Tests!"),
        (LanguageCode.ES, "¡Hola, Tests!"),
        (LanguageCode.FR, "Bonjour, Tests!"),
    ],
)
def test_greets_in_every_supported_language(lang, expected):
    assert Greeter("Tests").greet(lang) == expected


def test_defaults_to_english():
    assert Greeter("Tests").greet() == "Hello, Tests!"


def test_rejects_an_empty_name():
    with pytest.raises(ValueError):
        Greeter("")


if __name__ == "__main__":
    # Without SystemExit the exit code is dropped and the test always passes.
    raise SystemExit(pytest.main([__file__, "-q"]))
