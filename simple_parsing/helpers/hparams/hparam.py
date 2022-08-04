import dataclasses
from functools import wraps
from logging import getLogger
from typing import Any, Dict, List, Optional, Tuple, Type, TypeVar, Union, overload

from simple_parsing.helpers.fields import choice as _choice
from simple_parsing.helpers.fields import field

from .priors import CategoricalPrior, LogUniformPrior, NormalPrior, Prior, UniformPrior

logger = getLogger(__name__)
T = TypeVar("T")


class ValueOutsidePriorException(Exception):
    def __init__(self, value: Any, prior: Any, *args, **kwargs):
        self.value = value
        self.prior = prior
        super().__init__(*args, **kwargs)


@overload
def uniform(
    min: int,
    max: int,
    default: int = None,
    discrete: bool = True,
    strict: bool = False,
    shape: Union[int, Tuple[int, ...]] = None,
    **kwargs,
) -> int:
    pass


@overload
def uniform(
    min: float,
    max: float,
    default: float = None,
    strict: bool = False,
    shape: Union[int, Tuple[int, ...]] = None,
    **kwargs,
) -> float:
    pass


@overload
def uniform(
    min: float,
    max: float,
    default: float = None,
    discrete: bool = False,
    strict: bool = False,
    shape: Union[int, Tuple[int, ...]] = None,
    **kwargs,
) -> float:
    pass


def uniform(
    min: Union[int, float],
    max: Union[int, float],
    discrete: bool = None,
    default: Union[int, float, dataclasses._MISSING_TYPE] = dataclasses.MISSING,
    strict: bool = False,
    shape: Union[int, Tuple[int, ...]] = None,
    **kwargs,
) -> Union[int, float]:
    """Declares a Field with a Uniform prior.

    Parameters
    ----------
    min : Union[int, float]
        Minimum value.

    max : Union[int, float]
        Maximum value.

    discrete : bool, optional
        Whether this value is sampled discretely (an integer) or not. By default None, in
        which case the types of the `min`, `max` and `default` arguments
        will be used to infer whether the field should be discrete or not.

    default : Union[int, float], optional
        The default value to use. Not setting a value here makes this field a required
        argument of the dataclass. Setting a value can also be useful for the experiment
        version control feature of Orion. By default None.

    strict : bool, optional
        Whether the bounds should be strictly enforced. When set to True, attempting to
        create an object with this field, and passing a value outside the bounds will
        raise a ValueError.

    Returns
    -------
    Union[int, float]
        A `dataclasses.Field` object, with the prior stored in its metadata. The return
        type annotation is intentionally "wrong", so that the type checker doesn't raise
        errors when declaring fields on a dataclass, since their type annotations
        wouldn't match with the return type of this function.
    """
    # TODO: what about uniform over a "choice"?
    if "default_value" in kwargs:
        assert default in {
            None,
            dataclasses.MISSING,
        }, "can't pass both `default` and `default_value`"
        default = kwargs.pop("default_value")

    if discrete is None:
        # TODO: Set discrete = False by default, and then maybe set it to True later if
        # the annotation on the field is int.
        discrete = False
        if min == 0 and max == 1:
            discrete = False
        elif (isinstance(min, int) and isinstance(max, int)) and (
            default in {None, dataclasses.MISSING} or isinstance(default, int)
        ):
            # If given something like uniform(0, 100) or uniform(5,10,default=7) then
            # we can 'safely' assume that the discrete option should be used.
            discrete = True
    if shape and default not in {None, dataclasses.MISSING}:
        assert isinstance(shape, int), "only support int shapes for now."
        if isinstance(default, (int, float)):
            default = tuple(default for _ in range(shape))

    if discrete and default not in {None, dataclasses.MISSING}:
        if shape is None:
            default = round(default)
        else:
            assert isinstance(shape, int), "only support int shapes for now."
            default = tuple(round(default[i]) for i in range(shape))

    # TODO: Make sure this doesn't by accident make some fields behave as positional
    # fields
    default_v = None if default is dataclasses.MISSING else default

    prior = UniformPrior(min=min, max=max, discrete=discrete, default=default_v, shape=shape)

    # if default is None:
    #     default = dataclasses.MISSING
    #     default = (min + max) / 2

    return hparam(default=default, prior=prior, strict=strict, **kwargs)


@overload
def log_uniform(
    min: int,
    max: int,
    discrete: bool = True,
    shape: Union[int, Tuple[int, ...]] = None,
    **kwargs,
) -> int:
    pass


@overload
def log_uniform(
    min: float,
    max: float,
    discrete: bool = False,
    shape: Union[int, Tuple[int, ...]] = None,
    **kwargs,
) -> float:
    pass


def log_uniform(
    min: Union[int, float],
    max: Union[int, float],
    discrete: bool = False,
    default: Union[int, float, dataclasses._MISSING_TYPE] = dataclasses.MISSING,
    shape: Union[int, Tuple[int, ...]] = None,
    **kwargs,
) -> Union[int, float]:
    if "default_value" in kwargs:
        assert default in {
            None,
            dataclasses.MISSING,
        }, "can't pass both `default` and `default_value`"
        default = kwargs.pop("default_value")

    default_v = default
    if default is dataclasses.MISSING:
        default_v = None
    prior = LogUniformPrior(min=min, max=max, discrete=discrete, default=default_v, shape=shape)

    # TODO: Do we really want to set the default value when not passed?
    # if default in {None, dataclasses.MISSING}:
    #     log_min = math.log(min, prior.base)
    #     log_max = math.log(max, prior.base)
    #     default = math.pow(prior.base, (log_min + log_max) / 2)
    #     if discrete or (isinstance(min, int) and isinstance(max, int)):
    #         default = round(default)
    return hparam(
        default=default,
        prior=prior,
        **kwargs,
    )


loguniform = log_uniform


@wraps(_choice)
def categorical(
    *choices: T,
    default: Union[T, dataclasses._MISSING_TYPE] = dataclasses.MISSING,
    probabilities: Union[List[float], Dict[str, float]] = None,
    strict: bool = False,
    **kwargs: Any,
) -> T:
    """Marks a field as being a categorical hyper-parameter.

    This wraps the `choice` function from `simple_parsing`, making it possible to choose
    the value from the command-line.

    The probabilities for each value should be passed through this `probabilities`
    argument.

    Returns:
        T: the result of the usual `dataclasses.field()` function (a dataclass field).
    """
    if "default_value" in kwargs:
        assert default in {
            None,
            dataclasses.MISSING,
        }, "can't pass both `default` and `default_value`"
        default = kwargs.pop("default_value")

    metadata = kwargs.get("metadata", {})
    default_key = default

    options: List[Any]
    if len(choices) == 1 and isinstance(choices[0], dict):
        choice_dict = choices[0]
        if probabilities and not isinstance(probabilities, dict):
            raise RuntimeError(
                "Need to pass a dict of probabilities when passing a dict of choices."
            )
        # TODO: If we use keys here, then we have to add a step in __post_init__ of the
        # dataclass holding this field, so that it gets the corresponding value from the
        # dict.
        # IDEA: Adding some kind of 'hook' to be used by simple-parsing?

        def postprocess(value):
            if value in choice_dict:
                return choice_dict[value]
            return value

        metadata["postprocessing"] = postprocess
        if default not in {None, dataclasses.MISSING}:
            assert default in choice_dict.values()
            default_key = [k for k, v in choice_dict.items() if v == default][0]
        options = list(choice_dict.keys())
    else:
        options = list(choices)

    if isinstance(probabilities, dict):
        if abs(sum(probabilities.values()) - 1) > 1e-5:
            raise RuntimeError("Probabilities should sum to 1!")
        probs = []
        for option in options:
            probability = probabilities.get(option, 0.0)
            probs.append(probability)
        probabilities = probs

    default_v = default_key
    if default is dataclasses.MISSING:
        default_v = None

    prior = CategoricalPrior(
        choices=options,
        probabilities=probabilities,
        default_value=default_v,
    )
    metadata["prior"] = prior

    if strict:

        def postprocess(value):
            if value not in prior:
                raise ValueOutsidePriorException(value=value, prior=prior)
            return value

        if "postprocessing" not in metadata:
            metadata["postprocessing"] = postprocess
        else:
            # TODO: Compose both functions?
            existing_fn = metadata["postprocessing"]
            new_fn = postprocess
            metadata["postprocessing"] = lambda v: new_fn(existing_fn(v))

    kwargs["metadata"] = metadata
    return _choice(*choices, default=default, **kwargs)


def hparam(
    default: T,
    *args,
    prior: Union[Type[Prior[T]], Prior[T]] = None,
    strict: bool = False,
    **kwargs,
) -> T:
    metadata = kwargs.get("metadata", {})
    min: Optional[float] = kwargs.get("min", kwargs.get("min"))
    max: Optional[float] = kwargs.get("max", kwargs.get("max"))

    if prior is None:
        assert min is not None and max is not None
        # if min and max are passed but no Prior object, assume a Uniform prior.
        prior = UniformPrior(min=min, max=max)
        metadata.update(
            {
                "min": min,
                "max": max,
                "prior": prior,
            }
        )

    elif isinstance(prior, type) and issubclass(prior, (UniformPrior, LogUniformPrior)):
        # use the prior as a constructor.
        assert min is not None and max is not None
        prior = prior(min=min, max=max)

    elif isinstance(prior, Prior):
        metadata["prior"] = prior
        if isinstance(prior, (UniformPrior, LogUniformPrior)):
            metadata.update(
                dict(
                    min=prior.min,
                    max=prior.max,
                )
            )
        elif isinstance(prior, (NormalPrior)):
            metadata.update(
                dict(
                    mu=prior.mu,
                    sigma=prior.sigma,
                )
            )

    else:
        # TODO: maybe support an arbitrary callable?
        raise RuntimeError(
            "hparam should receive either: \n"
            "- `min` and `max` kwargs, \n"
            "- `min` and `max` kwargs and a type of Prior to use, \n"
            "- a `Prior` instance."
        )

    if strict:
        assert "postprocessing" not in metadata

        def postprocess(value):
            if value not in prior:
                raise ValueOutsidePriorException(value=value, prior=prior)
            return value

        metadata["postprocessing"] = postprocess

    kwargs["metadata"] = metadata
    assert "default" not in kwargs
    return field(
        default=default,
        *args,
        **kwargs,
    )
