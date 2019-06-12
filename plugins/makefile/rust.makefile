# Makefile for {binary}
# {author}{date}
#!
#! Lines starting with #! are not part of the template.
#! New will ignore these lines when processing the template.
#!

SHELL=bash
RUSTC=rustc
RUSTFLAGS=
binary={binary}
source={source_path}

.PHONY: all, debug, release
all: debug

debug: RUSTFLAGS+=-g
debug: $(binary)

release: RUSTFLAGS+=-O
release: $(binary)

$(binary): $(source)
	$(RUSTC) $(RUSTFLAGS) -o $(binary) $(source)

.PHONY: clean
clean:
	-@if [[ -e $(binary) ]]; then\
		if rm -f $(binary); then\
			printf "Binaries cleaned:\n    $(binary)\n";\
		fi;\
	else\
		printf "Binaries already clean:\n    $(binary)\n";\
	fi;

.PHONY: help, targets
help targets:
	-@printf "Make targets available:\n\
	all       : Build with no optimization or debug symbols.\n\
	clean     : Delete previous build files.\n\
	debug     : Build the executable with debug symbols.\n\
	release   : Build the executable with optimization, and strip it.\n\
	";
