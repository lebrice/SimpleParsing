""" TODO: Extract everything related to warm-starting / distances / etc. into a new
subclass of HyperParameters
"""
import dataclasses
from dataclasses import dataclass
from typing import Union, Dict
from .hyperparameters import HyperParameters
from simple_parsing.logging_utils import get_logger
from simple_parsing.helpers.serialization import Serializable
from simple_parsing.utils import dict_intersection
import numpy as np
logger = get_logger(__file__)


@dataclass
class WarmStarteableHParams(HyperParameters):
    """ WIP: Subclass of HyperParameters, that adds methods used when warm-starting HPO.
    """

    def distance_to(
        self,
        other: Union[HyperParameters, Dict],
        weights: Dict[str, float] = None,
        translate: bool = False,
    ) -> float:
        """Computes a 'distance' to another hyperparameter object or dictionary.

        Args:
            other (Union[): Another HyperParameters object
            weights (Dict[str, float], optional): Optional coefficients used to
                scale the distance with respect to each attribute/dimension.
                Defaults to None.
            translate (bool, optional): Wether or not to translate the other's
                attributes to match those of `self` before calculating the
                'distance'. Defaults to True.

        Returns:
            float: the distance as a float.
        """
        # return hp_distance(self, other, weights=weights, translate=translate)
        x1: Dict[str, float] = self.to_dict()

        if weights:
            if not translate:
                assert set(weights) <= set(
                    x1
                ), f"When given, the weights should match some of the fields of {x1} ({weights})"
        else:
            weights = {}

        # wether self and other are related through inheritance
        related = isinstance(other, type(self)) or isinstance(self, type(other))
        if isinstance(other, HyperParameters) and related:
            # Easiest case: the two are of the same type or related through
            # inheritance.
            x2: Dict[str, float] = other.to_dict()
        elif translate:
            raise NotImplementedError("Not using this 'translate' feature here yet.")
            translator = self.get_translator()
            logger.debug(f"x2 before: {other}")
            # 'Translate' the other into a dict with the same keys as 'self'
            x2 = translator.translate(other, drop_rest=True)
            if weights:
                logger.debug(f"weights before: {weights}")
                weights = translator.translate(weights, drop_rest=True)
                logger.debug(f"Weights after: {weights}")
            logger.debug(f"x2 after: {x2}")

        elif isinstance(other, Serializable):
            x2 = other.to_dict()
        elif dataclasses.is_dataclass(other):
            x2 = dataclasses.asdict(other)
        elif isinstance(other, dict):
            x2 = other
        else:
            raise NotImplementedError(
                f"Don't know how to calculate distance from self to {other}."
            )

        distance: float = 0.0
        assert weights is not None
        for k, (v1, v2) in dict_intersection(x1, x2):
            distance += weights.get(k, 1) * abs(v1 - v2)
        return distance

    def similarity(
        self, other: Union[Dict, "HyperParameters"], translate: bool = True
    ) -> float:
        """Cosine similarity between hparams. Translates `other` if needed.

        Args:
            other (Union[Dict, HyperParameters]): other hparam to compare to.
            translate (bool, optional): Wether to translate the keys from
                `other` which might describe the same attributes as `self`
                before calculating the similarity.
                Defaults to True.

        Returns:
            float: [description]
        """
        weights = {}
        for bound in self.get_bounds():
            # TODO: Do this differently for LogUniform priors, right?
            length = bound.domain[1] - bound.domain[0]
            if length == 0 or np.isposinf(length):
                # TODO
                raise NotImplementedError(
                    f"Domain of hparam {bound.name} is infinite: {bound}"
                )
            weights[bound.name] = 1 / length
        return 1 / (1 + self.distance_to(other, weights=weights, translate=translate))

    # @classmethod
    # def get_translator(cls) -> Translator[Union[Dict, "HyperParameters"], Dict]:
    #     return SimpleTranslator.get_translator(cls)

    def to_orion_trial(self):
        from orion.core.utils.format_trials import dict_to_trial
        return dict_to_trial(self.to_dict(), self.get_orion_space_dict())
