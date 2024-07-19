= @UPACKAGE@(1)
:man source:   @UCPACKAGE@
:man version:  @VERREV@
:man manual:   @UCPACKAGE@ Manual

// Secondary template file to make manpage.1
//
// See "AsciiDoc Syntax Quick Reference"
// https://docs.asciidoctor.org/asciidoc/latest/syntax-quick-reference/
// https://docs.asciidoctor.org/asciidoctor/latest/manpage-backend/

// convert by:
// $ asciidoctor --doctype manpage -b manpage -a 'newline=\n' @PACKAGE@.asciidoc

== NAME

@PACKAGE@ - program to do something

== SYNOPSIS

*@PACKAGE@*  [*-h*] ...


== DESCRIPTION

*@PACKAGE@* do something.

=== optional arguments:

*-h*, *--help*::
    show this help message and exit.


== AUTHOR

Copyright © @YEAR@ @FULLNAME@ <@EMAIL@>

== LICENSE

MIT License

== SEE ALSO

See also ...

