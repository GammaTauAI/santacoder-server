"""
Adapted from @mhyee. Originally from https://nuprl/TypeWeaver/main/SantaCoder/src/model.py

"""

import re

from model import Model

from typing import List

INFILL_MARKER = "_hole_"


class TypeInference:
    def __init__(self, model: Model, max_length: int = 2048, temperature: float = 1.0, mode: str = "PSM", num_comps: int = 1):
        self.model = model
        self.max_length = max_length
        self.temperature = temperature
        self.mode = mode
        self.num_comps = num_comps

    def clip_prompt(self, prefix: str, suffix: str, max_length: int):
        """
        Clip the prefix and suffix to be at most `max_length` tokens long.
        The start of the prefix should be clipped, and the end of the suffix
        should be clipped. If both already fit within `max_length`, then do
        nothing.
        """
        # we need at least 2 tokens to show something
        assert max_length >= 2

        # TODO: this encode-decode stuff is very inefficient,
        # but works for now for the current design

        # encode prefix and suffix
        prefix_t = self.model.tokenizer.encode(prefix)
        suffix_t = self.model.tokenizer.encode(suffix)

        prefix_len = len(prefix_t)
        suffix_len = len(suffix_t)

        if prefix_len + suffix_len <= max_length:
            # nothing to do
            return prefix, suffix

        # distribute 3/4 of the max length to the prefix and 1/4 to the suffix
        prefix_max = int(max_length * 0.75)
        suffix_max = max_length - prefix_max

        # remember: we want to clip the start of the prefix and the end of the suffix
        # also, if we have leftover of the prefix, we want to give it to the suffix
        prefix_len = min(prefix_max, prefix_len)
        suffix_len = min(suffix_max, suffix_len)

        # if we have leftover of the prefix, we want to give it to the suffix
        leftover = max_length - prefix_len - suffix_len
        suffix_len += leftover

        prefix_t = self.model.tokenizer.decode(prefix_t[:prefix_len])
        suffix_t = self.model.tokenizer.decode(suffix_t[-suffix_len:])

        return prefix_t, suffix_t

    def _generate_valid_types(self, prefix: str, suffix: str, retries: int) -> List[str]:
        """
        Given a prefix and suffix for infilling, try to generate a valid
        TypeScript type. We try `retries` times before
        giving up and returning `any`.
        """
        for _ in range(retries):
            generated = self.model.infill(
                [(prefix, suffix)] * self.num_comps, self.temperature, self.mode)

            checked_not_empty = []
            for g in generated:
                if g.strip() != "":
                    checked_not_empty.append(g.strip())

            if len(checked_not_empty) == 0:
                continue

            return checked_not_empty
        return ["any"]

    def _infill_one(self, template: str) -> List[str]:
        """
        Split the template at the infill point and construct the prefix and suffix.
        """
        parts = template.split(INFILL_MARKER, 1)
        if len(parts) < 2:
            raise ValueError(
                f"Expected at least one {INFILL_MARKER} in template, but got {template}"
            )

        infilled_prefix = parts[0]
        # TODO: generalize this for multiple languages (":" only works for typescript and python)
        suffix = parts[1].replace(": " + INFILL_MARKER, "")
        # Clip the prefix and suffix to make sure they fit into the prompt

        clipped_prefix, clipped_suffix = self.clip_prompt(
            infilled_prefix,
            suffix,
            self.max_length - 100,  # 100 tokens for the type generation
        )

        print(
            f"\tclipped left:\n {clipped_prefix}\n\tclipped right:\n {clipped_suffix}")

        filled_types = self._generate_valid_types(
            clipped_prefix, clipped_suffix, retries=3
        )
        return filled_types

    def infer(self, code: str) -> List[str]:
        """
        Given code, infer the first type annotation. Returns the type-annotation
        as a string.
        """
        if INFILL_MARKER not in code:
            return []
        return self._infill_one(code)


def infer(model: Model, code: str, num_comps: int, mode: str, max_length: int = 2048, temperature: float = 1.0) -> List[str]:
    """
    Generates `num_samples` type annotations for the first _hole_ in the given code.
    """
    assert num_comps > 0
    type_inf = TypeInference(model, max_length, temperature, mode, num_comps)
    return type_inf.infer(code)
