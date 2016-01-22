# -*- coding: utf-8 -*-

import json
import warnings


## Handle string with translations
# @todo define a default language that will be used in case the wanted language is not available for this string (gettext-like behavior)
class MlString(object):

    default_lang = '___'
    ## Instanciate a new string with translation
    #
    # @param translations dict: With key = lang and value the translation
    def __init__(self, translations=None, default_value = None):
        if isinstance(translations, str):
            try:
                translations = json.loads(translations)
            except ValueError:
                if default_value is None:
                    default_value = str(translations)
                    translations = None
        if translations is None:
            translations = dict()

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

    ## @return Default translation
    def get_default(self):
        return self.get(self.default_lang)
    
    ## @brief Set default value
    def set_default(self, text):
        self.set(self.default_lang, text)

    ## String representation
    # @return A json dump of the MlString::translations dict
    def __str__(self):
        return self.get_default()
    
    ## @brief Serialize the MlString in Json
    def json_dumps(self):
        if self.translations:
            return json.dumps(self.translations, sort_keys=True)
        else:
            return ""

    ## @brief Equivalent to json_dumps
    def dumps(self): return self.json_dumps()

    ## Test if two MlString instance are equivalent
    # @param other MlString|str : Another MlString instance or a string (json formated)
    # @return True or False
    def __eq__(self, other):
        if isinstance(other, str):
            other = MlString(other)

        if not isinstance(other, MlString):
            return False
        if not set(lng for lng in self.translations) == set( lng for lng in other.translations):
            return False
        for lng in self.translations:
            if self.get(lng) != other.get(lng):
                return False
        return True
    
    ## @brief Allow [] access to translations
    def __getitem__(self, langname): return self.get(langname)
    
    ## @brief Allow [] set 
    def __setitem__(self, langname, txt): return self.set(langname, txt)
    
    ## @brief Implements dict.keys() method
    def keys(self): return self.translations.keys()
        
    ## @brief Implements dict.values() method
    def values(self): return self.translations.values()
    
    ## @brief Implements dict.items() method
    def items(self): return self.translations.items()

    @staticmethod
    ## Instanciate a MlString from something
    # @deprecated Equivalent to MlString(translations = arg, default_value = None)
    def load(arg):
        return MlString(arg)
