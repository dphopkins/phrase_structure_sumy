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
            if line.isupper():
                heading = Sentence(line, self._tokenizer, is_heading=True)
                current_paragraph.append(heading)
            elif not line and current_paragraph:
                sentences = self._to_sentences(current_paragraph)
                # converts list of lines in current_paragraph to list of Sentences
                paragraphs.append(Paragraph(sentences))
                # converts list of Sentences to tuple of Sentences
                # stores that as a property of the Paragraph object
                # the Paragraph is added to the list of Paragraph objects (paragraphs)
                current_paragraph = []
            elif line:
                current_paragraph.append(line)

        sentences = self._to_sentences(current_paragraph)
        # converts list of lines in current_paragraph to list of Sentences
        paragraphs.append(Paragraph(sentences))
        # converts list of Sentences to tuple of Sentences
        # stores that as a property of the Paragraph object
        # the Paragraph is added to the list of Paragraph objects (paragraphs)
        
        ######################## ADDED BY DAN ########################
        for par in paragraphs:
            # print(self._to_sentence('Hey there.'))
            # par._sentences = (self._to_sentence('Hey there.'), self._to_sentence('You are my friend.'))
            par._sentences = self.getRealSentenceTuple(par._sentences)
            #print(par._sentences) # par._sentences is a tuple of Sentences
        ##############################################################

        return ObjectDocumentModel(paragraphs)
        # you can call Paragraph.sentences to get all the Sentences in that Paragraph

    ######################## ADDED BY DAN ########################
    def getRealSentenceTuple(self, sentences): # where sentences is a tuple of Sentences
        to_tuple = []
        for s in sentences: # for each Sentence
            converted = self.getNonOrthos(s) # function to get list of non-ortho Sentences
            # converted = [self._to_sentence('Hey there.'), self._to_sentence('You are my friend.')]
            for non_ortho in converted:
                to_tuple.append(non_ortho)
        return tuple(to_tuple) # convert Sentence list to tuple

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
        punctuation = text[-1] # keep track of punctuation of the ortho
        sentences = []

        grammar = load('file:grammar.cfg')
        parser = RecursiveDescentParser(grammar)

        words = self.tokenize_words(text) # tuple of words that make up a sentence (no punctuation though...not even commas)

        # num_options = len(words) + (len(words)-1) + ... + 1 = (len(words)/2) * (len(words) + 1)
        # algorithm is O(n^2)... let's try to make that better
        for i in range(0, len(words)):
            sofar = ''

            for j in range(i, len(words)):
                sofar += words[j]

                is_sentence = True
                try:
                    to_try = self.tokenize_words(sofar) # convert back to list of words
                    parser.parse(to_try) # see if this 'sentence' is a sentence
                except: # ValueError?
                    is_sentence = False

                if is_sentence:
                    the_sent = sofar.capitalize()
                    the_sent += punctuation
                    sentences.append(the_sent) # append the non-orthographic sentence to the list

                sofar += ' ' # get read for the next word

        sentences = self._to_sentences(sentences) # takes a list of sentences (strings) and returns a list of Sentences

        return sentences # list of all Sentences within the orthographic sentence
    ##############################################################

    def _to_sentences(self, lines):
        text = ""
        sentence_objects = []

        for line in lines:
            if isinstance(line, Sentence):
                if text:
                    sentences = self.tokenize_sentences(text)
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