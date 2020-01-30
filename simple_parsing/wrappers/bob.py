import dataclasses

@dataclasses.dataclass
class Bob:
    a: int

for field in dataclasses.fields(Bob):
    print(field.default)
