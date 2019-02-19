# Makefile for {binary}
# {author}{date}
#!
#! Lines starting with #! are not part of the template.
#! New will ignore these lines when processing the template.
#!

SHELL=bash
CC=yasm
LD=gcc
CFLAGS=-f elf64 -m amd64 -Worphan-labels
LDFLAGS=-Wall -static

binary={binary}
source={source}
objects=$(source:.asmc=.o)

$(binary): $(objects)
	$(LD) -o $(binary) $(LDFLAGS) $(objects)

all: $(binary)

debug: LDFLAGS+=-DDEBUG -g3
debug: CFLAGS+=-g dwarf2
debug: all

release: LDFLAGS+=-DNDEBUG -O3
release: CFLAGS+=
release: all
	@if strip $(binary); then\
		printf "\n%s was stripped.\n" "$(binary)";\
	else\
		printf "\nError stripping executable: %s\n" "$(binary)" 1>&2;\
	fi;

%.o: %.asmc
	$(CC) $(CFLAGS) -o $@ $<

.PHONY: clean
clean:
	-@if [[ -e $(binary) ]]; then\
		if rm -f $(binary); then\
			printf "Binaries cleaned: $(binary)\n";\
		fi;\
	else\
		printf "Binaries already clean: $(binary)\n";\
	fi;

	-@if ls $(objects) &>/dev/null; then\
		if rm $(objects); then\
			printf "Objects cleaned: $(objects)\n";\
		fi;\
	else\
		printf "Objects already clean: $(objects)\n";\
	fi;

.PHONY: cleanmake, makeclean
cleanmake makeclean:
	@make --no-print-directory clean && make --no-print-directory;

.PHONY: tags
tags:
	-@printf "Building ctags...\n";
	ctags -R .;

.PHONY: targets
targets:
	-@printf "Make targets available:\n\
	all       : Build with no optimization or debug symbols.\n\
	clean     : Delete previous build files.\n\
	cleanmake : Run \`make clean && make\`\n\
	makeclean : Alias for \`cleanmake\`\n\
	debug     : Build the executable with debug symbols.\n\
	release   : Build the executable with optimization, and strip it.\n\
	tags      : Build tags for this project using \`ctags\`.\n\
	";
