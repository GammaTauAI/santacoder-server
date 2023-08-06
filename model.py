"""
Written by @mhyee. Originally from https://nuprl/TypeWeaver/main/SantaCoder/src/model.py

"""

import os
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

from typing import Union

# This is necessary to avoid crazy warnings when the program creates a subprocess (forks).
os.environ["TOKENIZERS_PARALLELISM"] = "false"


def get_tokens_from_name(model_name):
    if "santacoder" in model_name:
        return ["<fim-prefix>", "<fim-middle>", "<fim-suffix>", "<fim-pad>"]
    elif "starcoder" in model_name:
        return ["<fim_prefix>", "<fim_middle>", "<fim_suffix>", "<fim_pad>"]
    else:
        raise ValueError(
            "Invalid model name. Must include either 'santacoder' or 'starcoder'.")


class Model:
    def __init__(
        self,
        max_tokens: int = 50,
        top_p: float = 0.95,
        device: Union[int, str, torch.device] = 0
    ):
        self.MODEL_NAME = "gammatau/santacoder-ts-fim"
        if os.environ.get("MODEL_NAME"):
            self.MODEL_NAME = os.environ["MODEL_NAME"]
        self.MODEL_REVISION = "main"
        toks = get_tokens_from_name(self.MODEL_NAME)
        self.FIM_PREFIX = toks[0]
        self.FIM_MIDDLE = toks[1]
        self.FIM_SUFFIX = toks[2]
        self.FIM_PAD = toks[3]
        self.ENDOFTEXT = "<|endoftext|>"
        self.max_tokens = max_tokens
        self.top_p = top_p
        self.device = device

        self.model = AutoModelForCausalLM.from_pretrained(
            self.MODEL_NAME,
            revision=self.MODEL_REVISION,
            trust_remote_code=True,
            torch_dtype=torch.bfloat16
        ).to(self.device)

        self.tokenizer = AutoTokenizer.from_pretrained(
            self.MODEL_NAME, padding_side="left")

        # Note that the special tokens must be listed in the order below.
        self.tokenizer.add_special_tokens({
            "additional_special_tokens": [
                self.ENDOFTEXT,
                self.FIM_PREFIX,
                self.FIM_MIDDLE,
                self.FIM_SUFFIX,
                self.FIM_PAD
            ],
            "pad_token": self.ENDOFTEXT,
        })

    def _extract_fim_part(self, s: str) -> str:
        """
        Find the index of <fim-middle>
        """
        start = s.find(self.FIM_MIDDLE) + len(self.FIM_MIDDLE)
        stop = s.find(self.ENDOFTEXT, start) or len(s)
        return s[start:stop]

    def infill(self, prefix_suffix_tuples, temperature: float = 1.0, mode: str = "PSM"):
        output_list = True
        if type(prefix_suffix_tuples) == tuple:
            prefix_suffix_tuples = [prefix_suffix_tuples]
            output_list = False

        if mode == "PSM":
            prompts = [f"{self.FIM_PREFIX}{p}{self.FIM_SUFFIX}{s}{self.FIM_MIDDLE}"
                       for p, s in prefix_suffix_tuples]
        elif mode == "SPM":  # variant 2
            prompts = [f"{self.FIM_PREFIX}{self.FIM_SUFFIX}{s}{self.FIM_MIDDLE}{p}"
                       for p, s in prefix_suffix_tuples]
        else:
            raise ValueError("Invalid mode. Must be PSM or SPM.")

        # `return_token_type_ids=False` is essential, or we get nonsense output.
        inputs = self.tokenizer(
            prompts,
            return_tensors="pt",
            padding=True,
            return_token_type_ids=False,
            truncation=True,
            max_length=self.model.config.n_positions - self.max_tokens - 1,
        ).to(self.device)
        max_length = inputs.input_ids[0].size(0) + self.max_tokens

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                do_sample=True,
                use_cache=True,
                top_p=self.top_p,
                temperature=temperature,
                max_length=max_length,
                pad_token_id=self.tokenizer.pad_token_id
            )
        # WARNING: cannot use skip_special_tokens, because it blows away the
        # FIM special tokens.
        result = [
            self._extract_fim_part(
                self.tokenizer.decode(tensor, skip_special_tokens=False))
            for tensor in outputs
        ]
        return result if output_list else result[0]
