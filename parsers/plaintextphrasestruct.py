# -*- coding: utf8 -*-

from __future__ import absolute_import
from __future__ import division, print_function, unicode_literals

from .._compat import to_unicode
from ..utils import cached_property
from ..models.dom import Sentence, Paragraph, ObjectDocumentModel
from .parser import DocumentParser

######################## ADDED BY DAN ########################
import nltk
from nltk import RecursiveDescentParser
from nltk.data import load
from nltk import word_tokenize
from nltk import pos_tag
##############################################################

class PlaintextParser(DocumentParser):
    """
    NON-ORTHOGRAPHIC (PHRASE-STRUCTURE) PARSING FOR SUMMARIES
    
    Parses simple plain text in following format:

    HEADING
    This is text of 1st paragraph. Some another sentence.

    This is next paragraph.

    HEADING IS LINE ALL IN UPPER CASE
    This is 3rd paragraph with heading. Sentence in 3rd paragraph.
    Another sentence in 3rd paragraph.

    Paragraphs are separated by empty lines. And that's all :)
    """

    @classmethod
    def from_string(cls, string, tokenizer):
        return cls(string, tokenizer)

    @classmethod
    def from_file(cls, file_path, tokenizer):
        with open(file_path) as file:
            return cls(file.read(), tokenizer)

    def __init__(self, text, tokenizer):
        super(PlaintextParser, self).__init__(tokenizer)
        self._text = to_unicode(text).strip()

    @cached_property
    def significant_words(self):
        words = []
        for paragraph in self.document.paragraphs:
            for heading in paragraph.headings:
                words.extend(heading.words)

        if words:
            return tuple(words)
        else:
            return self.SIGNIFICANT_WORDS

    @cached_property
    def stigma_words(self):
        return self.STIGMA_WORDS

    @cached_property
    def document(self):
        current_paragraph = []
        paragraphs = []

        for line in self._text.splitlines(): # splits at newline
            line = line.strip() # gets rid of whitespace
            if not line and current_paragraph: # end of paragraph
                sentences = self._to_sentences(current_paragraph)
                # converts list of lines in current_paragraph to list of Sentences
                paragraphs.append(Paragraph(sentences))
                # converts list of Sentences to tuple of Sentences
                # stores that as a property of the Paragraph object
                # the Paragraph is added to the list of Paragraph objects (paragraphs)
                current_paragraph = [] # reset paragraph
            else:
                current_paragraph.append(line)

        # for last paragraph
        sentences = self._to_sentences(current_paragraph)
        paragraphs.append(Paragraph(sentences))
        
        sentences_so_far = 0
        list_of_indices = []
        ### LOOK HERE IF THERE ARE PROBLEMS
        for par in paragraphs:
            # print(par._sentences) # full tuple of sentences in each paragraph
            orthographic_sentences = self.getRealSentenceTuple(par._sentences)
            par._sentences = orthographic_sentences[0] # the sentences themselves
            indexes = orthographic_sentences[1] # the indexes within the paragraph of the original sentence the ortho belongs to
            for i in range(0, len(indexes)):
                indexes[i] += sentences_so_far

            if indexes: sentences_so_far = indexes[-1] + 1
            list_of_indices.append(indexes)

            # print(par._sentences) # par._sentences is a tuple of Sentences
        
        # list_of_indices is now a list of all the indices of the orthos (gives position of original sentence)
        # return ObjectDocumentModel(paragraphs) # original
        return ObjectDocumentModel(paragraphs), list_of_indices
        ##############################################################
        # you can call Paragraph.sentences to get all the Sentences in that Paragraph

    ######################## ADDED BY DAN ########################
    def getRealSentenceTuple(self, sentences): # where sentences is a tuple of Sentences
        to_tuple = []
        original_sentence_number = 0 # unsure if it should start on 0 or 1
        originals = [] # keeps track of the original sentence number in the paragraph
        for s in sentences: # for each Sentence
            converted = self.getNonOrthos(s) # function to get list of non-ortho Sentences
            for non_ortho in converted:
                to_tuple.append(non_ortho)
                originals.append(original_sentence_number)
            original_sentence_number += 1
        # print(originals) # list of sentence indexes
        tupled = tuple(to_tuple) # convert Sentence list to tuple
        return tupled, originals

    def getNonOrthos(self, sentence): # where sentence is a Sentence
        """ Converts a Sentence into a list of sub-orthographic Sentence(s)

        THIS IS WHAT THE ALGORITHM LOOKS LIKE:

        Jim made dinner while Joe went out and Brad slept.
        ---------------
        ----------------------------------
        -------------------------------------------------
                              ------------
                              ---------------------------
                                               ----------


        """
        text = sentence._text # the actual sentence text (string)
        sentences = []
        words = word_tokenize(text)
        punctuation = words[-1] # keep track of punctuation of the ortho
        words = words[:-1]

        grammar = load('file:grammar.cfg')
        parser = RecursiveDescentParser(grammar)
        # ChartParser takes ~45 minutes to parse and summarize a 500 word doc vs. ~3 seconds for RDParser

        # num_options = len(words) + (len(words)-1) + ... + 1 = (len(words)/2) * (len(words) + 1)
        # algorithm is O(n^2)... let's try to make that better
        for i in range(0, len(words)):
            sofar = ''

            for j in range(i, len(words)):
                current = words[j]
                if any(sym in current for sym in (",", "'s", ":")): sofar = sofar[:-1]
                elif current == "'ve": words[j] = "have"
                elif current == "n't": words[j] = "not"
                elif current == "'ll": words[j] = "will"

                # assume apostrophe is for possesion
                elif current == "'" and words[j-1][-1] == "s": sofar = sofar[:-1]

                elif current == "'d":
                    if nltk.pos_tag([words[j+1]])[0][1] == 'VBN':
                        words[j] = "had"
                    else:
                        words[j] = "would"

                sofar += words[j]

                # ensures that each sentence is at least two words long and doesn't end in a comma
                if i != j and not any(sym in current for sym in (",", ":", ";", "'", "'s", "'d", "'ll", "'ve")):
                    is_sentence = True
                    try:
                        to_try = self.tokenize_words(sofar) # convert back to list of words
                        parser.parse(to_try) # see if this 'sentence' is a sentence
                    except ValueError: # ValueError?
                        is_sentence = False
                        # print("SENTENCE REJECTED BY GRAMMAR")

                    if is_sentence:
                        # capitalize() makes proper nouns lower case so we'll do our own capitalization
                        the_sent = sofar[0].upper() + sofar[1:]
                        # the_sent = sofar.capitalize()
                        the_sent += punctuation
                        sentences.append(the_sent) # append the non-orthographic sentence to the list

                sofar += ' ' # get read for the next word

        # ORIGINAL METHOD
        # sentences = self._to_sentences(sentences) # takes a list of sentences (strings) and returns a list of Sentences
        # self._to_sentences incorrectly converts some sentences
        # this results in things like Paul suffered a. Paul suffered a shoulder.
        # old method incorrectly assumes that it's being passed a line
        # however, we know we are passing a sentence

        # NEW METHOD
        # sentences is a list of strings
        # sentences is created for every paragraph
        sentences = map(self._to_sentence, sentences)

        return sentences # list of all Sentences within the orthographic sentence
    ##############################################################

    def _to_sentences(self, lines):

        text = ""
        sentence_objects = []

        for line in lines:
            if isinstance(line, Sentence):
                if text:
                    sentences = self.tokenize_sentences(text)
                    print(sentences)
                    sentence_objects += map(self._to_sentence, sentences)

                sentence_objects.append(line)
                text = ""
            else:
                text += " " + line

        text = text.strip()
        if text:
            sentences = self.tokenize_sentences(text)
            sentence_objects += map(self._to_sentence, sentences)

        return sentence_objects

    def _to_sentence(self, text):
        assert text.strip()
        return Sentence(text, self._tokenizer)
