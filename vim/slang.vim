"if exists("b:current_syntax")
"    finish
"endif

let b:current_syntax = "slang"

syn match slang_number '\<[+-]\=\d\+'
syn match slang_number '\<\zs[+-]\=\d\+\.\d*'

syn match slang_define '\(^\s*\|{\s*\|,\_s*\)\zs[a-zA-Z_][a-zA-Z_0-9]*\s*\ze:'
syn match slang_special '\[\|\]\|{\|}\|,\|:\|(\|)\|;'
syn match slang_operator '+\|-\|/\|\*\|='
syn region slang_string start='"' end='"'
syn region slang_comment start="/\*" end="\*/"
syn match slang_comment "//.*$"
syn keyword slang_kw let in import function namespace true false this
syn keyword slang_cond if then else


hi def link slang_special        Special
hi def link slang_operator       Operator
hi def link slang_number         Number
hi def link slang_string         String
hi def link slang_comment        Comment
hi def link slang_kw             Keyword
hi def link slang_cond           Conditional
hi def link slang_name           Tag
