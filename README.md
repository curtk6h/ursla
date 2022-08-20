# Ursla (UniveRsally Shitty Language)

A dirt simple language that's easy to understand and interpret.

## They aren't defects, they're features!

* NO bloat

    *With extremely limited syntax and built-in functionality, it's incredibly lightweight and staightforward to implement in another better language. Also, the compiler for Ursla is written in Ursla, so no additional porting is required.*

* NO tokenizing / NO trees (ie. parse tree or AST) / NO safety nets (ie. type checking)

    *By only having single character "keywords" there's little need for tokenizing code before compilation. Also, the grammar was designed around being easy to compile, and only requires a lookahead in one or two spots.*

* NO "short circuiting" of logical expressions

    *Sure it means the expressions are evaluated in full every time, but execution time will be constant!*

* NO base-10 integer literals, only hexidecimal

    *This may sound horrible but hey, at least it's not only base-10, so you can still spell out funny words in your numbers (ex. `+deadbeef`). Just make sure numbers starting with a - f are prefixed with a `+` or the parser will freak out :(*

* NO whitespace

    *Space or newline character indicate the end of a statement and that's it, so you don't have to decide how to space things.*

* NO string or map or boolean types

    *Enjoy the charm of more primitive primitives.*

* NO classes

    *Who needs 'em when you have fun and completely unenforced coding patterns.*

* NO FOR loops or other super useful syntaxes/constructs that are widely-offered

    *Don't get me wrong, I like FOR loops, lambdas, list comprehensions, etc., but they're all gravy.*

## Is there any practical reason to use this language?

No, I can't think of one. Ursla is meant to be a toy and work-of-art and not much more. I will say, that because it's such a dumb language, it'd be quite easy to tailor to a custom need if you have one. Other than that, it could possibly serve as an example for someone interested in learning the very basics of compilers and languages.

## Disclaimer / About the author

Hi. I don't have a whole lot of expertise on compilers. I took a class many years ago on the subject, and learned about language grammars and did an exercise using yacc or javacc (don't remember which one), but that's about it. Because of this, Ursla was especially fun to work on, with lots of room for creativity and exploration.