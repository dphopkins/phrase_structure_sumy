# -*- coding: utf8 -*-

from __future__ import absolute_import
from __future__ import division, print_function, unicode_literals


from collections import namedtuple
from operator import attrgetter
from ..utils import ItemsCount
from .._compat import to_unicode
from ..nlp.stemmers import null_stemmer


SentenceInfo = namedtuple("SentenceInfo", ("sentence", "order", "rating",))


class AbstractSummarizer(object):
    def __init__(self, stemmer=null_stemmer):
        if not callable(stemmer):
            raise ValueError("Stemmer has to be a callable object")

        self._stemmer = stemmer

    def __call__(self, document, sentences_count):
        raise NotImplementedError("This method should be overriden in subclass")

    def stem_word(self, word):
        return self._stemmer(self.normalize_word(word))

    def normalize_word(self, word):
        return to_unicode(word).lower()

    ############################# CHANGED BY DAN ############################
    def _get_best_sentences(self, sentences, rating, *args, **kwargs):
        # self = LuhnPhraseStruct
        # sentences = LuhnPhraseStruct.document.sentences
        # rating = LuhnPhraseStruct.rate_sentence
        # args are significant words
        
        rate = rating
        if isinstance(rating, dict):
            assert not args and not kwargs
            rate = lambda s: rating[s]

        infos = (SentenceInfo(s, o, rate(s, *args, **kwargs))
            for o, s in enumerate(sentences))

        # sort sentences by rating in descending order
        infos = sorted(infos, key=attrgetter("rating"), reverse=True)
        
        length = 0
        summary = "" # only used to check if text is a substring
        new_infos = []

        # PROBLEM IS THAT WE DON'T WANT OVERLAPPING SENTENCES

        for i in infos:
                
            # i.sentence is the Sentence
            text = i.sentence._text

            # if the text is not a substring of the summary...
            if text not in summary:
                    # all statement is probably incorrect:  and not all(ni.sentence._text not in text for ni in new_infos)


                    new_summary_length = length + len(text.split())

                    # if we've reached max summary length...
                    if new_summary_length == 100:
                        length += len(text.split()) # number of words
                        summary += text
                        new_infos.append(i)
                    # if the next sentence would make the summary too long
                    elif new_summary_length > 100: 
                        pass
                    # otherwise, add it and keep looking
                    else:
                        length += len(text.split()) # number of words
                        summary += text
                        new_infos.append(i)

        infos = new_infos

        # sort sentences by their order in document
        infos = sorted(infos, key=attrgetter("order"))
        for i in infos:
            print(i.order)

        return tuple(i.sentence for i in infos)
    #########################################################################
