#!/Users/grzegorz/Projects/Whisper/venv/bin/python
from parser import WhisperParser
from runtime import evaluate
from util import WRException


input = '1 + 2'
parser = WhisperParser(method='LALR')

if __name__ == '__main__':
    try:
        node = parser.parse(input)
        output = evaluate(('call', node, []))
        print output.raw
    except WRException as e:
        print e.message
