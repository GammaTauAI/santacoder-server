"""
Adapted from @mhyee. Originally from https://nuprl/TypeWeaver/main/SantaCoder/src/model.py

"""

import re
import subprocess
from subprocess import PIPE

from model import Model

from typing import List

class TypeInference:
    INFILL_MARKER = "_hole_"
    FUNC_START_REGEX = re.compile(r"^.*function(\s+([a-zA-Z_$][\w_$]*))?\s*\(")

    def __init__(self, model):
        self.model = model

    def _templatize_function(self, line: str) -> str:
        """
        If the line contains 'function(x, y, z)' then, then insert ???
        (or whatever INFILL_MARKER is) at the infill points,
        e.g. returning 'function(x???, y???, z???)'
        """
        # Find the first occurrence of "function("
        match = self.FUNC_START_REGEX.search(line)
        if match is None:
            return line
        function_start = match.end()

        # Find the first occurrence of ")"
        function_end = line.find(")", function_start)

        # Multi-line signature or no parameters
        if function_end == -1 or function_start == function_end:
            return line

        param_list = line[function_start:function_end].split(",")
        param_list = f"{self.INFILL_MARKER},".join(param_list) + self.INFILL_MARKER
        return line[:function_start] + param_list + line[function_end:]

    def _clip_text(self, str1: str, str2: str, max_length: int):
        """
        Clips the two strings so that the total length is at most max_length.
        Keeps the first string intact, and clips the second string if possible
        """
        def _prefix_ending_with_newline(str, max_length):
            """
            Produces a prefix of str that is at most max_length,
            but does not split a line.
            """
            return str[:max_length].rsplit("\n", 1)[0]

        def _suffix_starting_with_newline(str, max_length):
            """
            Produces a suffix of str that is at most max_length,
            but does not split a line.
            """
            return str[-max_length:].split("\n", 1)[0]

        # Find the last occurrence of "function" in str1
        enclosing_function_start = str1.rfind("function")
        str1 = str1[enclosing_function_start:]

        if len(str1) < max_length:
            # str1 is short enough, so clip str2
            str2 = _prefix_ending_with_newline(str2, max_length - len(str1))
        elif len(str2) < max_length:
            # str1 is too long but str2 is short enough, so clip str1
            str1 = _suffix_starting_with_newline(str1, max_length - len(str2))
        else:
            # Both exceed the max_length
            str1 = _suffix_starting_with_newline(str1, max_length // 2)
            str2 = _prefix_ending_with_newline(str2, max_length // 2)
        return str1, str2

    def _generate_valid_type(self, prefix: str, suffix: str, retries: int) -> str:
        """
        Given a prefix and suffix for infilling, try to generate a valid
        TypeScript type. To determine if it is valid, we use an external
        program, bundled with our InCoder script. We try `retries` times before
        giving up and returning `any`.
        """
        for _ in range(retries):
            generated = self.model.infill((prefix, suffix))
            print(generated)

            # Split on whitespace and keep only the first element
            generated = generated.split()[0]
            print(generated)
            if generated == "":
                continue

            return generated.strip()
        return "any"

    def _infill_one(self, template: str) -> str:
        """
        Split the template at the infill point and construct the prefix and suffix.
        """
        parts = template.split(self.INFILL_MARKER, 1)
        print(parts)
        if len(parts) < 2:
            raise ValueError(
                f"Expected at least one {self.INFILL_MARKER} in template, but got {template}"
            )

        infilled_prefix = parts[0]
        # TODO: generalize this for multiple languages (":" only works for typescript and python)
        suffix = parts[1].replace(": " + self.INFILL_MARKER, "")
        # Clip the prefix and suffix to make sure they fit into the prompt

        print(f"\tleft:\n {infilled_prefix}\n\tright:\n {suffix}")

        clipped_prefix, clipped_suffix = self._clip_text(
            infilled_prefix, suffix, self.model.max_context_length
        )
        filled_type = self._generate_valid_type(
            clipped_prefix, clipped_suffix, retries=3
        )
        return filled_type

    def infer(self, code: str) -> str:
        """
        Given code, infer the first type annotation. Returns the type-annotation
        as a string.
        """
        if self.INFILL_MARKER not in code:
            return code
        return self._infill_one(code)


m = Model()
type_inf = TypeInference(m)

def infer(code: str, num_samples: int) -> List[str]:
    """
    Generates `num_samples` type annotations for the first _hole_ in the given code.
    """
    assert num_samples > 0 
    type_annotations: List[str] = []
    while num_samples > 0:
        type_annotation = type_inf.infer(code)
        type_annotations += [type_annotation]
        num_samples -= 1
    return type_annotations
