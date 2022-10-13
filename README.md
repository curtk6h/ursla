# Ursla (UniveRsally Shitty LAnguage)

A dirt simple language that's easy to understand and interpret.

## They aren't defects, they're features!

* NO bloat

    *With extremely limited syntax and built-in functionality, it's incredibly lightweight and staightforward to implement in an actual programming language. Also, the compiler for Ursla is written in Ursla, so no additional porting is required.*

* NO tokenizing / NO syntax trees / NO safety nets

    *By having only single character operators, there's little need for tokenizing code as a first step. Also, the grammar was designed to be easy to compile and only requires a lookahead in one or two spots.*

* NO "short circuiting" of logical expressions

    *Sure it means the expressions are evaluated in full every time, but execution time will be constant!*

* NO base-10 integer literals, only hexidecimal

    *This sounds horrible and I assure you it is, but at least you can spell out funny words in your numbers (ex. `+deadbeef`). Just make sure numbers starting with a-f are prefixed with a `+` or it's a syntax error :(*

* NO whitespace

    *Space or newline character indicate the end of a statement and that's it, so you don't have to decide how to space things.*

* NO string, map, or boolean types -- only integer, data, and array

    *Enjoy the charm of more primitive primitives.*

* NO classes

    *Who needs 'em when you have fun and completely unenforced coding patterns.*

* NO for-loops or other super useful syntaxes/constructs that are widely offered, loved, and depended on

    *Why would I bother to implement these things when there aren't even base-10 numbers.*

## Examples

### Hello world
```
:out{ $\85 }
out("hello world")
```

### Fibonacci sequence
```
:out{ $\85 }
:array{ $\89 }
:set{ $\8c }
:fibonacci_number(n){
  ?n=0{ $0 }
  :a:0
  :b:1
  ?n>1{
    :c:a+b
    :a:b
    :b:c
    :n:n-1
  }^
  $b
}
:fibonacci_sequence(n){
  :seq:array(n)
  :i:0
  ?i<n{
    set(seq,i,fibonacci_number(i))
    :i:i+1
  }^
  $seq
}
out(fibonacci_sequence(10))
```

## Syntax

| Construct | Description |
| - | - |
| `?x{ ... }` | if then |
| `?x{ ... }:{ ... } ` | if then else |
| `?x{ ... }:?y{ ... } ` | if then else-if |
| `?x{ ... }^` | while repeat |
| `?{ !x }:{ !x ... }` | try throw catch |
| `+ff`, `100`, `-1` | integer literal (hexadecimal)|
| `"hello world"` | ascii data literal |
| `[backtick]foo.png[backtick]` | file data literal |
| `,x,y,z` | array literal |
| `\80` | built-in operation by code|
| `(...)` | expression group |
| `:x` | declare variable |
| `:x:y` | set variable |
| `:x{ ... }` | function |
| `:x(a,b,c){ ... }` | function with arguments |
| `$x` | return from call |
| `x(a,b,c)` | call |
| `x&y`, `x\|y`, `x^y`, `~x` | logical operations |
| `x<y`, `x>y`, `x=y` | comparison operations |
| `x+y`, `x-y`, `x*y`, `x/y`, `x%y`, `-x` | arithmetic operations |

## Built-in functions

| Name | Description |
| - | - |
| `is(x,y)` | is x physically the same thing as y |
| `weak(x)` | get an untracked reference to x, to avoid circular references that simple reference counting can't handle |
| `hash(x)` | get hash code for x |
| `time()` | get milliseconds elapsed since start of program |
| `in()` | read full input as data |
| `out(x)` | write text representation of x to output |
| `pack(x,y,m)` | pack masked bits from y into x, at mask position |
| `unpack(x,m)` | unpack masked bits from x |
| `data(n)` | allocate data of length n
| `array(n)` | allocate array of length n
| `len(x)` | get length of data/array x |
| `get(x,i)` | get element at position i from data/array x |
| `set(x,i,y)` | set element at position i from data/array x, to y |
| `copy(x,y,xi,yi,n)` | copy elements from data/array y to x |
| `load(k)` | load data from persistent storage |
| `save(k,x)` | save data to persistent storage |
| `fin(f)` | read data from file |
| `fout(f,x)` | write data to file |
| `b64(x)` | encode data as base64 |
| `b64decode(x)` | decode data from base64 |

## Is there any practical reason to use this language?

Nope! Ursla is meant to be a toy and work-of-art and not much more.
