from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import typing
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Text

from rasa_nlu.extractors import EntityExtractor
from rasa_nlu.model import Metadata


if typing.TYPE_CHECKING:
    from duckling import DucklingWrapper


DUCKLING_DIMENSIONS = ["time", "temperature", "number", "ordinal", "distance", "volume",
                       "amount-of-money", "duration", "email", "url", "phone-number"]


class DucklingExtractor(EntityExtractor):
    """Adds entity normalization by analyzing found entities and transforming them into regular formats."""

    name = "ner_duckling"

    context_provides = {
        "process": ["entities"],
    }

    output_provides = ["entities"]

    def __init__(self, duckling_dimensions=DUCKLING_DIMENSIONS, duckling=None):
        # type: (Text, Optional[DucklingWrapper]) -> None

        # If duckling dimensions == [] or == None
        if not duckling_dimensions:
            duckling_dimensions = DUCKLING_DIMENSIONS
        self.duckling_dimensions = duckling_dimensions
        self.duckling = duckling

    @classmethod
    def required_packages(cls):
        # type: () -> List[Text]
        return ["duckling"]

    @classmethod
    def create(cls, duckling_dimensions=DUCKLING_DIMENSIONS):
        unknown_dimensions = [dim for dim in duckling_dimensions if dim not in DUCKLING_DIMENSIONS]
        if len(unknown_dimensions) > 0:
            raise ValueError("Invalid duckling dimension. Got '{}'. Allowed: {}".format(
                ", ".join(unknown_dimensions), ", ".join(DUCKLING_DIMENSIONS)))

        return DucklingExtractor(duckling_dimensions)

    @classmethod
    def cache_key(cls, model_metadata):
        # type: (Metadata) -> Text

        return cls.name + "-" + model_metadata.language

    def pipeline_init(self, language):
        # type: (Text, Text) -> None
        from duckling import DucklingWrapper

        if self.duckling is None:
            try:
                self.duckling = DucklingWrapper(language=language)  # languages in duckling are eg "de$core"
            except ValueError as e:
                raise Exception("Duckling error. {}".format(e.message))

    def process(self, text, entities):
        # type: (Text, List[Dict[Text, Any]]) -> Dict[Text, Any]

        extracted = []
        if self.duckling is not None:
            matches = self.duckling.parse(text)
            relevant_matches = [match for match in matches if match["dim"] in self.duckling_dimensions]
            for match in relevant_matches:
                entity = {"start": match["start"],
                          "end": match["end"],
                          "value": match["value"]["value"],
                          "entity": match["dim"]}

                extracted.append(entity)

        extracted = self.add_extractor_name(extracted)
        return {
            "entities": entities.extend(extracted)
        }

    @classmethod
    def load(cls, duckling_dimensions=DUCKLING_DIMENSIONS):
        # type: (Text) -> DucklingExtractor

        return cls.create(duckling_dimensions)
