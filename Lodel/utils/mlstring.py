# -*- coding: utf-8 -*-

import json
import warnings


## Handle string with translations
# @todo define a default language that will be used in case the wanted language is not available for this string (gettext-like behavior)
class MlString(object):

    default_lang = '__default__'
    ## Instanciate a new string with translation
    #
    # @param translations dict: With key = lang and value the translation
    def __init__(self, translations=None, default_value = None):
        if translations is None:
            translations = dict()
        elif isinstance(translations, str):
            translations = json.loads(translations)

        if not isinstance(translations, dict):
            raise ValueError('Bad value given for translations argument on MlString instanciation')
        else:
            self.translations = translations

        self.translations[self.default_lang] = '' if default_value is None else default_value
        if default_value is None:
            warnings.warn('No default value when isntanciating an MlString')
    
    ## Return a translation
    # @param lang str: The lang
    # @return An empty string if the wanted lang don't exist
    # @warning Returns an empty string if the wanted translation didn't exists
    # @todo if the asked language is not available, use the default one, defined as a class property
    def get(self, lang = None):
        if lang is None or lang not in self.translations:
            lang = self.default_lang
        return self.translations[lang]
    
    ## Set a translation for this MlString
    # @param lang str: The language
    # @param text str: The translation
    # @todo check if the default language as a translation
    def set(self, lang, text):
        if not text:
            if lang in self.translations:
                del(self.translations[lang])
        else:
            self.translations[lang] = text

    def set_default(self, text):
        self.set(self.default_lang, text)

    def __repr__(self):
        return self.__str__()

    ## String representation
    # @return A json dump of the MlString::translations dict
    def __str__(self):
        if self.translations:
            return json.dumps(self.translations, sort_keys=True)
        else:
            return ""

    ## Test if two MlString instance are equivalent
    # @param other MlString|str : Another MlString instance or a string (json formated)
    # @return True or False
    def __eq__(self, other):
        if isinstance(other, str):
            other = MlString.load(other)

        if not isinstance(other, MlString):
            return False
        if not set(lng for lng in self.translations) == set( lng for lng in other.translations):
            return False
        for lng in self.translations:
            if self.get(lng) != other.get(lng):
                return False
        return True

    @staticmethod
    ## Instanciate a MlString from json
    # @param json_string str: Json datas in a string
    # @return A new MlString instance
    # @warning fails silently
    def load(json_string):
        if isinstance(json_string, str) and json_string != '':
            translations = json.loads(json_string)
        else:
            translations = dict()
        return MlString(translations)
