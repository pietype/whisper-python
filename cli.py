#!/Users/grzegorz/Projects/Whisper/venv/bin/python
import sys
import logging

from parser import WhisperParser
from runtime import evaluate
from util import WRException

logging.getLogger('whisper').disabled = True
parser = WhisperParser(method='LALR')

if __name__ == '__main__':
    input = None
    try:
        _program, file_name = sys.argv
        with open(file_name) as f:
            input = f.read()
            node = parser.parse(input)
            output = evaluate(('call', node, []))
            print output.raw
    except WRException as e:
        sys.stderr.write(e.message)
        exit(1)
    except ValueError as e:
        sys.stderr.write('''Usage:
whisper file
''')
        exit(1)
