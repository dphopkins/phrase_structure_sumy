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
    def _get_best_sentences(self, sentences, indices, rating, *args, **kwargs):
        # self = LuhnPhraseStruct
        # sentences = LuhnPhraseStruct.document.sentences
        # indices = [[0, 0, 1, 1, 1], [2, 2, 2, 2], ...]
        # rating = LuhnPhraseStruct.rate_sentence
        # args are significant words

        new_indices = []
        for par in indices:
            for i in par:
                new_indices.append(i)
        indices = new_indices # [0,0,1,1,1,2,2,2,2]
        
        rate = rating
        if isinstance(rating, dict):
            assert not args and not kwargs
            rate = lambda s: rating[s]

        # length of indices and sentences are equal
        infos = []
        for i in range(0, len(indices)):
            s = sentences[i]
            o = indices[i]
            si = SentenceInfo(s, o, rate(s, *args, **kwargs))
            infos.append(si)

        # sort sentences by rating in descending order
        infos = sorted(infos, key=attrgetter("rating"), reverse=True)
        
        length = 0
        summary = "" # only used to check if text is a substring
        new_infos = []

        for i in infos:
                
            # i.sentence is the Sentence
            text = i.sentence._text

            # if the text is not a substring of the summary...
            if text not in summary:

                if any(i.order == ni.order for ni in new_infos):
                    # TODO: IF THE SENTENCE HAS BEEN USED BEFORE
                    # TODO: right now, we use sentence # as order...
                    # TODO: that won't work if we start accepting
                    # TODO: multiple ps-sents from the same ortho
                    # TODO: since they will have the same "order"
                    # TODO: but when we put them back together
                    # TODO: we need to know the actual order!
                    pass
                else: # if the index (sentence) has not been used before
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

        return tuple(i.sentence for i in infos)
    #########################################################################
