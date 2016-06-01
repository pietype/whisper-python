[x] Split Object/Function from dict
      Remain close in syntax and semantic
      Model after list native
[ ] Split `+` method at Whisper level
      Currently split by checking raw (python) type
[x] Import
[ ] re module
  [x] Basic automaton
[x] List
  [x] map
  [x] create_list has to take expressions
  [x] reduce
  [x] Map return value problem - reduce not in scope
[ ] Dict
  [x] get
  [ ] Figure out interface around dict
[x] Lazy evaluation vs Failing expressions
  [x] Rewrite failed automaton implementation
  [x] Implement then 
    [x] object
    [x] failed
[ ] Reflection
[ ] Better error message
  [ ] Root cause
  [ ] Stack trace
[ ] Print objects
[x] Refactor test_parser
[x] Refactor test_lexer
[ ] Write better lexer tests
      I messed up the tests by trying to reuse expressions from the parser tests.
    Write tests that actually test lexer logic.
[ ] Refactor whisper code out of runtime
      Preferably use pure whisper
  [ ] Native interface
[ ] Interactive Debugger
  [ ] Debug interface
  [ ] CLI
[x] Fix default arguments
[ ] Release
  [ ] setup.py
