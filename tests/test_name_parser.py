from core.name_parser import extract_name


def test_extract_name_drops_trailing_intent_phrase():
    text = "I am chandrasekhar. Looking for DL appointment."
    assert extract_name(text) == "chandrasekhar"


def test_extract_name_simple_full_name():
    text = "my name is Mary Jane Watson"
    assert extract_name(text) == "Mary Jane Watson"


def test_extract_name_short_reply():
    assert extract_name("Alex") == "Alex"
