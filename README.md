Whisper programming language python interpreter

1. Development/Installation
  0. Prerequisites

    Python 2.7
    virtualenv 14.0.6
    
  1. Running some code
    
    First thing you need to do is setup the hashbang inside `cli.py` to
    point to the correct instance of python. Then create a symlink to
    this file inside your bin directory
    
    `sudo ln -s /local/path/to/cli.py /usr/local/bin/whisper`
    
    Create a script, for example `hello.w`, then you can execute it with
    
    `whisper hello.w`
    
2. Tutorial

  1. Hello world
  
    So far Whisper has no io support to speak of, instead the result of module's 
    evaluation gets printed to the output stream, or the error gets printed to the 
    error stream.
     
    At the end of every function in Whisper, and a module is one, there's an expression.
    The current Hello World is then:
     
    ```whisper
    # hello.w - Hello world module. Everything after a # is a comment btw
    'Hello world!'
    ```
     
  2. Basic syntax
    Scripts are called `modules`, because they can be imported. Every reference name is
    valid with the exception  some interpunction and the word `import`. This means that
    both `+` and `+1` are valid reference names, which in turn means that `1+1` has to be
    writtern as `1 + 1` or `1+ 1`.
    There's no assignment operator, but `:` covers the syntax for setting up constants. 
    Object traversal through a dot, Java style:
    
    ```whisper
    # basicSyntax.w
    n: 1      # makes `n` reference available
              # this is where the definition block ends, single expression is next
    n.length  # method 'length' of Number
    ```
    
    Method and function calls both handled by parentheses, arguments beyond first 
    require explicit naming:
    
    ```whisper
    # calls.w
    [].length()                  # method call with no arguments, evaluates to 0
    nextNumber(1)                # some function call with a single argument
    addStrings('a', other: 'b')  # call with more than one argument
    ```
    
    Infix notation handled by syntax sugar resolving them to method calls
    
    ```whisper
    # infix.w - examples of infix calls and their equivalents
    1 + 2 + 3  # 1.+(2).+(3) 
    2 + 2 * 2  # 2.+(2).*(2) and evaluates to 8, operator priority not implemented yet
    # [] length  # syntax error, needs argument
    ```
  
    Braces `{` `}` used both for dictionaries and function bodies, irrelevant indentation. 
    Newline `\n` acts as a separator, so does comma `,`. All commas optional.
    
    No special character used for newline to not act as a separator, instead an expression can
    be broken on either on a dot `.` or after the operator in an infix call
    
    ```whisper
    # newlines.w - continuations
    1 + 1        # normal expression
    1 +
        1        # twoline expression
    o.m()        # normall call
    o.
      m()        # twoline call
    ```
    
  3. Basic types
  
    There are Numbers, Strings, Lists, Dictionaries and Functions. Functions also serve as
    Objects by a bit of witchcraft/by design. Every basic type is an object.
    
    ```whisper
    # basicTypes.w - Built in objects examples
    number0: 0               # currently only integers, will support floats also
    string1: 'String'        # very basic - no escapes etc. 
    string2: "Other string"  # same here, could have semantics
    list1: []                # empty list
    list2: [0, 1, 2]         # single line list
    list3: ['Red'            # newlines act as separators
            'Green',         # but commas are optional
            'Blue']          #
    dict1: {}                # empty dict, notice no parens in front
    dict2: {'a': 3, 'b': 1}  # comma as separator, expressions as keys
    dict3: {'Title': 'Pulp Fiction'
            'Director': 'Quentin Tarantino'
            'Year': 1994}    # no date type yet
    ```
    
    Functions are distinguished from dictionaries by the argument list (in braces) that 
    preceds the body inside the curly braces. You might be shocked to learn that every 
    argument beside the first needs a default value.
    
    ```whisper
    function1: (){ 0 }                 # empty argument list
    function2: (a){ a }                # single argument with no default
    function3: (a: 1){ a }             # single argument with default value
    function4: (a, b: 0){ a + 1 }      # two arguments
    # brokenFunction: (a, b){ a + b }  # syntax error, need default value for b
    ```
    
    You can define constants local to the function inside the body, just like in a module
    
    ```whisper
    function5: (){
      a: 1
      b: 2
      
      a + b
    }
    ```
    
    Actually the connection to the module goes deeper, but let's first look at objects.
    They are basically defined by their constructors, which are functions with no 
    expressions. They evaluate to a new instance of the object when called.
    
    ```whisper
    Object: (){
      item: 0
      method: (){ self.item }  # item alone is not in scope
    }
    # Object().method()        # this evaluates to 0
    ```
    
    We'll get to the call syntax, semantics and what self is in the next chapter.
    If you are wondering why you cannot just reference item I don't have a reason right
    now as it was required by an earlier prototype and I didn't yet decide how I want to
    handle it. 
