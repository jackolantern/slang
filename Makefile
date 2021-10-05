.PHONY: test
test: slang/parser.py
	poetry run nosetests

slang/parser.py: slang.ebnf
	python -m tatsu slang.ebnf -o slang/parser.py
