from typing import NewType

Character = NewType("Character", str)

def per_char_formatter(c: Character) -> Character:
    """ This function will format each character both in expected and student's outputs """
    return c

def full_output_formatter(output: str) -> str:
    """ This function will format both the entire expected and entire student's outputs"""
    return output
