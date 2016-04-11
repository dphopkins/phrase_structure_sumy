# -*- coding: utf8 -*-

from __future__ import absolute_import
from __future__ import division, print_function, unicode_literals


from collections import namedtuple
from operator import attrgetter
from ..utils import ItemsCount
from .._compat import to_unicode
from ..nlp.stemmers import null_stemmer


def longest_common_substring(s1, s2):
    """ Thanks to: https://en.wikibooks.org/wiki/Algorithm_Implementation/Strings/Longest_common_substring#Python """
    m = [[0] * (1 + len(s2)) for i in xrange(1 + len(s1))]
    longest, x_longest = 0, 0
    for x in xrange(1, 1 + len(s1)):
        for y in xrange(1, 1 + len(s2)):
            if s1[x - 1] == s2[y - 1]:
                m[x][y] = m[x - 1][y - 1] + 1
                if m[x][y] > longest:
                    longest = m[x][y]
                    x_longest = x
            else:
                m[x][y] = 0
    return s1[x_longest - longest: x_longest]


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
                
                matches = []
                for ni in new_infos:
                    if i.order == ni.order:
                        matches.append(ni)

                # now matches is the list of info objects
                # that have the same order as i

                if matches:
                    # pass
                    # TODO: RETHINK THIS ALGORITHM
                    accept = True
                    for m in matches:
                        x = longest_common_substring(text, m.sentence._text)
                        x = len(x.split())
                        if x > (.25*len(text.split())) or x > 4: # if 25% or more overlap or 5 or more words of overlap
                            accept = False
                            break

                    if accept:
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
                    else:
                        pass


                    # longest_common_substring(s1, s2) returns overlap
                    # we want the len() of the split() of that

                    # go through the matches and compare with text
                    # TODO: IF THE SENTENCE HAS BEEN USED BEFORE
                    # TODO: right now, we use sentence # as order...
                    # TODO: that won't work if we start accepting
                    # TODO: multiple ps-sents from the same ortho
                    # TODO: since they will have the same "order"
                    # TODO: but when we put them back together
                    # TODO: we need to know the actual order!
                    

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
