# TODO dictionary can only handle simple nodes
# implement Node with get/match method

Automaton: (states){
  match: (input, state: 0){
    _me: me  # TODO figure out better scoping
    states[state][input[0]] then
      (next){ next = states.length() or
        _me(input[1:], state: next) }
  }
}
