# Makefile for {binary}
# {author}{date}
#!
#! Lines starting with #! are not part of the template.
#! New will ignore these lines when processing the template.
#!

SHELL=bash
CC=gcc
CFLAGS=-Wall -Wextra -Wfloat-equal -Winline -Wlogical-op \
       -Wmissing-include-dirs -Wnull-dereference -Wpedantic -Wshadow \
       -Wstrict-prototypes -Wunused-macros \
       -U_FORTIFY_SOURCE -D_FORTIFY_SOURCE=2 \
       -std=c11
LIBS=

binary={binary}
source={source}
objects:=$(source:.c=.o)

.PHONY: all, debug, release
all: debug

debug: tags
debug: CFLAGS+=-g3 -DDEBUG
debug: $(binary)

release: CFLAGS+=-O3 -DNDEBUG
release: $(binary)

$(binary): $(objects)
	$(CC) -o $(binary) $(CFLAGS) $(objects) $(LIBS)

%.o: %.c
	$(CC) -c $< $(CFLAGS) $(LIBS)

tags: $(source)
	-@printf "Building ctags...\n";
	ctags -R $(source);

.PHONY: clean
clean:
	-@if [[ -e $(binary) ]]; then\
		if rm -f $(binary); then\
			printf "Binaries cleaned:\n    $(binary)\n";\
		fi;\
	else\
		printf "Binaries already clean:\n    $(binary)\n";\
	fi;

	-@if ls $(objects) &>/dev/null; then\
		if rm $(objects); then\
			printf "Objects cleaned:\n";\
			printf "    %s\n" $(objects);\
		fi;\
	else\
		printf "Objects already clean:\n";\
		printf "    %s\n" $(objects);\
	fi;

.PHONY: strip
strip:
	@if strip $(binary); then\
		printf "\n%s was stripped.\n" "$(binary)";\
	else\
		printf "\nError stripping executable: %s\n" "$(binary)" 1>&2;\
	fi;

.PHONY: help, targets
help targets:
	-@printf "Make targets available:\n\
	all       : Build with no optimization or debug symbols.\n\
	clean     : Delete previous build files.\n\
	debug     : Build the executable with debug symbols.\n\
	release   : Build the executable with optimization, and strip it.\n\
	strip     : Run \`strip\` on the executable.\n\
	tags      : Build tags for this project using \`ctags\`.\n\
	";
