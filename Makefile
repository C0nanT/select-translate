.PHONY: start test hooks

# runs attached to the terminal: Ctrl+C or closing the terminal stops it
start:
	python3 -u pc/translator.py

# unit tests (no GTK/network)
test:
	python3 -m unittest discover -s pc/tests -v

# enables the pre-push hook versioned in hooks/ (once per clone; safe to repeat)
hooks:
	git config core.hooksPath hooks
	chmod +x hooks/pre-push
