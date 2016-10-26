#!/usr/bin/python
# coding: utf-8

"""
Usage:
    yatr [options] [<text> ...]

Options:
    -h --help                   Show help information
    --from, -f LANG             Bla
    --to, -t LANG               Bla
    --stdout                    Bla
    --send-notify               Bla
    --raw                       Bla
    --debug                     Bla
    --list-languages            Bla
    --default-language LANG     Bla [default: en]

Arguments:
    <text>                      Bla-Bla
"""


import os
import sys
import time
import subprocess
import requests
import json

from collections import defaultdict

import notify2
import docopt

import services_api


YANDEX_TRANSLATE_TOKEN = "trnsl.1.1.20140825T115227Z.c7fe0ce90716a1de.31220cde4c709b4df87609907ed7de1281613376"
YANDEX_DICTIONARIES_TOKEN = "dict.1.1.20150407T073308Z.38da1cbb95482c30.e56d3996644cadc7c7c887a47b82829cb72be9cf"

ya_translator = services_api.YandexTranslatorAPI(YANDEX_TRANSLATE_TOKEN)
ya_dictionaries = services_api.YandexDictionaryAPI(YANDEX_DICTIONARIES_TOKEN)


def get_selection():
    process = subprocess.Popen(['xsel'], stdout=subprocess.PIPE)
    selection, _ = process.communicate()
    return selection


def send_notify(title, message, speed=300, min_delay=10):
    notify2.init("yatr")
    notification = notify2.Notification(title, message)
    notification.show()
    time.sleep(max(
        len(title.split() + message.split()) * 60 / speed,
        min_delay
    ))
    notification.close()


def write_output(text, translation, lang, mode):
    if mode == 'raw':
        print translation
        return

    from_, to = lang.split('-')

    output_part_A = u"[{}] {}".format(from_, text)
    output_part_B = u"[{}] {}".format(to, translation)

    if mode == 'notify':
        send_notify(output_part_A, output_part_B)
    elif mode == 'stdout':
        print output_part_A
        print output_part_B


def show_langs():
    directions = defaultdict(list)

    for lang in ya_translator.get_langs():
        from_, to = lang.split('-')
        directions[from_].append(to)

    for from_ in sorted(directions.keys()):
        print "{}: {}".format(from_, ", ".join(sorted(directions[from_])))


def get_options():
    options = docopt.docopt(__doc__)

    if options['--debug']:
        sys.stderr.write(repr(options) + '\n')

    if options['--list-languages']:
        show_langs()
        exit()

    answer = {}
    if options['<text>']:
        answer['text'] = " ".join(options['<text>']).decode('utf-8')
    else:
        answer['text'] = get_selection().decode('utf-8')
    answer['text_lang'] = ya_translator.detect(answer['text'])

    if options['--to'] is None:
        if answer['text_lang'] == 'ru':
            answer['to'] = options['--default-language']
        else:
            answer['to'] = 'ru'
    else:
        answer['to'] = options['--to']

    answer['from'] = options['--from']

    if answer['from'] is not None:
        answer['lang'] = "{from}-{to}".format(**answer)
    elif answer['text_lang']:
        answer['lang'] = "{text_lang}-{to}".format(**answer)
    else:
        raise ValueError('Unknown language')

    if options['--send-notify']:
        answer['output_mode'] = 'notify'
    elif options['--stdout']:
        answer['output_mode'] = 'stdout'
    elif options['--raw']:
        answer['output_mode'] = 'raw'
    else:
        answer['output_mode'] = 'notify'

    if options['--debug']:
        sys.stderr.write(repr(answer) + '\n')

    return answer


def lookup_in_dictionary(text, lang):
    article = ya_dictionaries.lookup(text, lang)

    if not article:
        return None

    def shorten(word):
        if word == u'существительное':
            return u'сущ'
        elif word == u'прилагательное':
            return u'прил'
        elif word == u'глагол':
            return u'глаг'
        else:
            return word[:5]

    bodytext = ""
    for defi in article:
        if 'pos' in defi:
            bodytext += '[%s] ' % shorten(defi['pos'])
        if 'gen' in defi:
            bodytext += '('+defi['gen']+') '
        for tr in defi["tr"]:
            bodytext += tr["text"]+', '
        bodytext += '\n'

    return bodytext.rstrip('\n')


if __name__ == '__main__':
    options = get_options()

    try:
        dictionary_translation = lookup_in_dictionary(
            options['text'],
            options['lang']
        )
    except services_api.YandexDictionaryException:
        dictionary_translation = None

    if dictionary_translation is not None:
        text = options['text']
        translation = dictionary_translation
    else:
        response = ya_translator.translate(
            options['text'],
            options['lang']
        )

        text = options['text']
        translation = response['text'][0]

    write_output(
        text,
        translation,
        options['lang'],
        options['output_mode']
    )
