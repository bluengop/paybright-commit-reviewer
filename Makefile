## Makefile - Paybright Commit review
SHELL := '/bin/bash'

## Targets: 
.PHONY: help requirements run

## Function to print help
#
#	awk /^[a-z_-]+:/				= Searches for lines that start with one or more lowercase alphabetic characters
#							    followed by a colon (target names).
#	{ printf "\033[1;33m%s\033[0m\n", $$0		= Prints the line that matches the first pattern (target name) in bold yellow.
#	flag = 1; next }				= Sets the "flag" variable to 1 to indicate that we're in the section of interest,
#							    and then skips to the next line.
#	flag && /^\#/					= If the "flag" is set to 1 (indicating we're in the section of interest) and
#							    the line starts with a "#" character...
#	{ sub(/^\#*/, "", $$0)				= ...Removes all "#" characters from the string...
#	print; next }					= ...And prints the line that matches the second pattern (lines starting with "#"),
#							    skipping to the next line.
# 	{ if (flag)					= If none of the previous patterns match, it executes the last part of the awk script:
#		flag = 0				    - since we're no longer in the section of interest, sets "flag" to 0.
#		print "" }				    - prints an empty (new) line to separate this printing from the next.
#
define PRINT_HELP
	awk '/^[a-z_-]+:/ {
    		printf "\033[1;33m%s\033[0m\n", $$0
    		flag = 1
    		next
		}

		flag && /^\#/ {
			sub(/^\#*/, "", $$0)
			print
	    	next
		}

		{
		    if (flag) {
        		flag = 0
        		print ""
    		}
	}' $(MAKEFILE_LIST)
endef
export PRINT_HELP


help:
## Prints help
	@printf "\n\e[1;32mTargets in this Makefile:\e[0m\n\n"
	@bash -c "$$PRINT_HELP"
	@echo

requirements:
## Installs the Python requirements from "requirements.txt" file
#   you'll need to have "pip" installed already in your system.
	pip3 install -r requirements.txt

run:
## Runs script "audit-export.py" with three arguments:
#   1. Personal Access Token (PAT). A token to access GitHub repos.
#   2. Repo name. The name of the repository: 'Paybright/Looker_paybright_project'.
#   3. Filename. The name for the file created as a result: 'export.csv'.
#   4. Branch. Git branch inside the repository given in arg 2.
#   5. Number of reviews. Required amount of reviews.
	python3 audit-export.py
