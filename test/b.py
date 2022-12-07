from dataclasses import dataclass
from simple_parsing import ArgumentParser
from .a import A

@dataclass
class B(A):
    v: int

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_arguments(B, 'b')
    args = parser.parse_args()
    print(args.b)