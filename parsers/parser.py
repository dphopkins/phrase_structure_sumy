# -*- coding: utf8 -*-

from __future__ import absolute_import
from __future__ import division, print_function, unicode_literals


class DocumentParser(object):
    """Abstract parser of input format into DOM."""

    SIGNIFICANT_WORDS = (
        "significant", # "významný"
        "excellent", # "vynikající"
        "substantial", # "podstatný"
        "distinguished", # "význačný"
        "important", # "důležitý"
        "famous", # "slavný"
        "interesting", # "zajímavý"
        "eminent", # "eminentní"
        "influential", # "vlivný"
        "super", # "supr"
        "best", # "nejlepší"
        "good", # "dobrý"
        "quality", # "kvalitní"
        "optimum", # "optimální"
        "relevant", # "relevantní"
    )
    STIGMA_WORDS = (
        "worst", # "nejhorší"
        "evil", # "zlý"
        "nasty", # "šeredný"
    )

    def __init__(self, tokenizer):
        self._tokenizer = tokenizer

    def tokenize_sentences(self, paragraph):
        return self._tokenizer.to_sentences(paragraph)

    def tokenize_words(self, sentence):
        return self._tokenizer.to_words(sentence)
