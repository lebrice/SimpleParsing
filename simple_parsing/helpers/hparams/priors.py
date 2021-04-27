import math
from abc import abstractmethod
from dataclasses import dataclass
from typing import Generic, List, Optional, TypeVar, Union, overload, Any
import random

numpy_installed = False
try:
    import numpy as np
    numpy_installed = True
except ImportError:
    pass


T = TypeVar("T")


@dataclass  # type: ignore
class Prior(Generic[T]):
    def __post_init__(self):
        if numpy_installed:
            self.np_rng = np.random
        else:
            self.rng: random.Random = random.Random()

    @abstractmethod
    def sample(self) -> T:
        pass

    def seed(self, seed: Optional[int]) -> None:
        # Should this seed this individual prior?
        if numpy_installed:
            self.np_rng = np.random.RandomState(seed)
        else:
            self.rng = random.Random(seed)

    @abstractmethod
    def get_orion_space_string(self) -> str:
        """ Gets the 'Orion-formatted space string' for this Prior object. """

    @abstractmethod
    def __contains__(self, v: Union[T, Any]) -> bool:
        pass


@dataclass
class NormalPrior(Prior):
    mu: float = 0.
    sigma: float = 1.
    discrete: bool = False
    default: Optional[float] = None

    def sample(self) -> Union[float, int]:
        if numpy_installed:
            value = self.np_rng.normal(self.mu, self.sigma)
        else:
            value = self.rng.normalvariate(self.mu, self.sigma)
        if self.discrete:
            return round(value)
        return value

    def get_orion_space_string(self) -> str:
        raise NotImplementedError(
            "TODO: Add this for the normal prior, didn't check how its done in "
            "Orion yet."
        )

    def __contains__(self, v: Union[T, Any]) -> bool:
        # TODO: For normal priors, I guess we only really check if the value is a float?
        return isinstance(v, (int, float))


@dataclass
class UniformPrior(Prior):
    min: float = 0.
    max: float = 1.
    discrete: bool = False
    default: Optional[float] = None

    def __post_init__(self):
        assert self.min <= self.max

    def sample(self) -> Union[float, int]:
        # TODO: add suport for enums?
        if numpy_installed:
            value = self.np_rng.uniform(self.min, self.max)
        else:
            value = self.rng.uniform(self.min, self.max)
        if self.discrete:
            return round(value)
        return value

    def get_orion_space_string(self) -> str:
        string = f"uniform({self.min}, {self.max}"
        if self.discrete:
            string += ", discrete=True"
        if self.default is not None:
            string += f", default_value={self.default}"
        string += ")"
        return string

    def __contains__(self, v: Union[T, Any]) -> bool:
        # TODO: Include the max value here? or not?
        return isinstance(v, (int, float)) and (self.min <= v < self.max)


@dataclass
class CategoricalPrior(Prior[T]):
    choices: List[T]
    probabilities: Optional[List[float]] = None
    default_value: Optional[T] = None

    def __post_init__(self):
        super().__post_init__()
        if isinstance(self.choices, dict):
            choices = []
            self.probabilities = []
            for k, v in self.choices.items():
                choices.append(k)
                assert isinstance(v, (int, float)), "probs should be int or float"
                self.probabilities.append(v)

    @overload
    def sample(self, n: int) -> List[T]: ...
    @overload
    def sample(self) -> T: ...

    def sample(self, n: int = None) -> Union[T, List[T]]:
        assert self.choices
        # n = n or 1
        # assert isinstance(n, int), n
        choices: List = []
        probabilities: List[float] = []
        if isinstance(self.choices, dict):
            for k, v in self.choices.items():
                choices.append(k)
                probabilities.append(v)
        else:
            choices = self.choices
            probabilities = self.probabilities

        print(choices, n, probabilities)
        if numpy_installed:
            s = self.np_rng.choice(choices, size=n, p=probabilities)
            samples = [(s_i.item() if isinstance(s_i, np.ndarray) else s_i) for s_i in s]
        else:
            samples = self.rng.choices(choices, weights=probabilities, k=n or 1)

        return samples[0] if n in {None, 1} else samples

    def get_orion_space_string(self) -> str:
        string = "choices("
        if self.probabilities:
            prob_dict = dict(zip(self.choices, self.probabilities))
            assert sum(self.probabilities) == 1, "probs should sum to 1."
            # BUG: Seems like orion still samples entries, even if they have zero
            # probability!
            # TODO: Remove the entries that have zero prob?
            prob_dict = {k: v for k, v in prob_dict.items() if v > 0}
            string += str(prob_dict)
        else:
            string += str(self.choices)
        if self.default_value is not None:
            assert isinstance(self.default_value, (int, str, float))
            default_value_str = str(self.default_value)
            if isinstance(self.default_value, str):
                default_value_str = f"'{self.default_value}'"
            string += f", default_value={default_value_str}"
        string += ")"
        return string

    def __contains__(self, v: Union[T, Any]) -> bool:
        return v in self.choices


@dataclass
class LogUniformPrior(Prior):
    min: float = 1e-3
    max: float = 1e+3
    base: float = math.e
    discrete: bool = False
    default: Optional[float] = None

    def sample(self) -> float:
        # TODO: Might not be 100% numerically stable.
        assert self.min > 0, "min of LogUniform can't be negative!"
        assert self.min < self.max, "max should be greater than min!"
        if numpy_installed:
            log_val = self.np_rng.uniform(self.log_min, self.log_max)
        else:
            log_val = self.rng.uniform(self.log_min, self.log_max)
        value = math.pow(self.base, log_val)
        if self.discrete:
            return round(value)
        return value

    @property
    def log_min(self) -> Union[int, float]:
        if numpy_installed:
            if self.base in {np.e, math.e}:
                log_min = np.log(self.min)
            else:
                log_min = np.log(self.min)
        else:
            if self.base is math.e:
                log_min = math.log(self.min)
            else:
                log_min = math.log(self.min, self.base)
        assert isinstance(log_min, (int, float))
        return log_min

    @property
    def log_max(self) -> Union[int, float]:
        if numpy_installed:
            if self.base in {math.e, np.e}:
                log_max = np.log(self.max)
            else:
                log_max = np.log(self.max) / np.log(self.base)
        else:
            if self.base is math.e:
                log_max = math.log(self.max)
            else:
                log_max = math.log(self.max, self.base)
        assert isinstance(log_max, (int, float))
        return log_max

    def get_orion_space_string(self) -> str:
        def format_power(value: float, log_value: float):
            if isinstance(value, int) or value.is_integer():
                return int(value)
            elif isinstance(log_value, int) or log_value.is_integer():
                log_value = int(log_value)
                if self.base == np.e:
                    return f"np.exp({int(log_value)})"
                elif self.base == 10:
                    return f"{value:.2e}"
            if math.log10(value).is_integer():
                return f"{value:.0e}"
            else:
                return f"{value:g}"

        min_str = format_power(self.min, self.log_min)
        max_str = format_power(self.max, self.log_max)
        string = f"loguniform({min_str}, {max_str}"
        if self.discrete:
            string += ", discrete=True"
        if self.default is not None:
            string += f", default_value={self.default}"
        string += ")"
        return string

    def __contains__(self, v: Union[T, Any]) -> bool:
        return isinstance(v, (int, float)) and (self.min <= v < self.max)
