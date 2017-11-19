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

all: $(source)
	$(RUSTC) $(RUSTFLAGS) -o $(binary) $(source)

debug: RUSTFLAGS+=-g
debug: all

release: RUSTFLAGS+=-O
release: all

.PHONY: clean
clean:
	-@if [[ -e $(binary) ]]; then\
			if rm -f $(binary); then\
					printf "Binaries cleaned.\n";\
			fi;\
	else\
			printf "Binaries already clean.\n";\
	fi;

.PHONY: cleanmake, makeclean
cleanmake makeclean:
	@make --no-print-directory clean && make --no-print-directory;

.PHONY: targets
targets:
	-@printf "Make targets available:\n\
	all       : Build with no optimization or debug symbols.\n\
	clean     : Delete previous build files.\n\
	cleanmake : Run \`make clean && make\`\n\
	makeclean : Alias for \`cleanmake\`\n\
	debug     : Build the executable with debug symbols.\n\
	release   : Build the executable with optimization, and strip it.\n\
	";
