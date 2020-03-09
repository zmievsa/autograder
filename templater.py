import re


matcher = re.compile("{% *([A-Za-z0-9_]+) *%}")


def format_template(template, **kwargs):
    for match in matcher.finditer(template):
        attr = match.group(1)
        value = kwargs.pop(attr, None)
        if value is None:
            raise ValueError(f"Attribute {attr} not supplied")
        template = template.replace(match.group(0), str(value))
    if len(kwargs):
        raise ValueError("Too many arguments supplied: " + ", ".join(kwargs.keys()))
    return template
