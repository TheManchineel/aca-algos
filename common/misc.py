def from_yn(x: str):
    return True if x.lower() in ["y", "yes"] else False if x.lower() in ["n", "no"] else None

def to_yn(x: bool):
    return "Yes" if x else "No"