Automaton: (states){
  match: (input, state: 0){
    _me: me
    states[state].match(input[0:1]) then (next){ next = states.length() or _me(input[1:], state: next) }
  }
}

Node: (state){
  match: (input){
    state[input[0:1]]
  }
}
