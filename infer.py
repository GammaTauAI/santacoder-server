"""
Adapted from @mhyee. Originally from https://nuprl/TypeWeaver/main/SantaCoder/src/model.py

"""

import re

from model import Model

from typing import List

INFILL_MARKER = "_hole_"


class TypeInference:
    FUNC_START_REGEX = re.compile(r"^.*function(\s+([a-zA-Z_$][\w_$]*))?\s*\(")

    def __init__(self, model, max_length: int = 2048, temperature: float = 1.0):
        self.model = model
        self.max_length = max_length
        self.temperature = temperature

    def clip_prompt(self, prefix: str, suffix: str, max_length: int):
        """
        Clip the prefix and suffix to be at most `max_length` characters long.
        The start of the prefix should be clipped, and the end of the suffix
        should be clipped. If both already fit within `max_length`, then do
        nothing.
        """

        prefix_len = len(prefix)
        suffix_len = len(suffix)
        if prefix_len + suffix_len <= max_length:
            return prefix, suffix  # Nothing to do

        max_suffix_length = int(max_length / 2)
        max_prefix_length = max_length - max_suffix_length

        if prefix_len > max_prefix_length:
            prefix = prefix[-max_prefix_length:]

        if suffix_len > max_suffix_length:
            suffix = suffix[:max_suffix_length]

        return prefix, suffix

    def _generate_valid_type(self, prefix: str, suffix: str, retries: int, mode: str) -> str:
        """
        Given a prefix and suffix for infilling, try to generate a valid
        TypeScript type. To determine if it is valid, we use an external
        program, bundled with our InCoder script. We try `retries` times before
        giving up and returning `any`.
        """
        for _ in range(retries):
            generated = self.model.infill(
                (prefix, suffix), self.temperature, mode)

            generated_strip = generated.strip()
            if generated_strip == "":
                continue

            return generated.strip()
        return "any"

    def _infill_one(self, template: str, mode: str) -> str:
        """
        Split the template at the infill point and construct the prefix and suffix.
        """
        parts = template.split(INFILL_MARKER, 1)
        print(parts)
        if len(parts) < 2:
            raise ValueError(
                f"Expected at least one {INFILL_MARKER} in template, but got {template}"
            )

        infilled_prefix = parts[0]
        # TODO: generalize this for multiple languages (":" only works for typescript and python)
        suffix = parts[1].replace(": " + INFILL_MARKER, "")
        # Clip the prefix and suffix to make sure they fit into the prompt

        print(f"\tleft:\n {infilled_prefix}\n\tright:\n {suffix}")

        clipped_prefix, clipped_suffix = self.clip_prompt(
            infilled_prefix, suffix, self.max_length
        )

        print(
            f"\tclipped left:\n {clipped_prefix}\n\tclipped right:\n {clipped_suffix}")

        filled_type = self._generate_valid_type(
            clipped_prefix, clipped_suffix, retries=3, mode=mode
        )
        return filled_type

    def infer(self, code: str, mode: str) -> str:
        """
        Given code, infer the first type annotation. Returns the type-annotation
        as a string.
        """
        if INFILL_MARKER not in code:
            return ""
        return self._infill_one(code, mode=mode)


def infer(model, code: str, num_samples: int, mode: str, max_length: int = 2048, temperature: float = 1.0) -> List[str]:
    """
    Generates `num_samples` type annotations for the first _hole_ in the given code.
    """
    assert num_samples > 0
    type_inf = TypeInference(model, max_length, temperature)
    type_annotations: List[str] = []
    while num_samples > 0:
        type_annotation = type_inf.infer(code, mode=mode)
        type_annotations += [type_annotation]
        num_samples -= 1
    return type_annotations
