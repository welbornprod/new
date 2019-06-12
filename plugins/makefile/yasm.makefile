# Makefile for {binary}
# {author}{date}
#!
#! Lines starting with #! are not part of the template.
#! New will ignore these lines when processing the template.
#!

SHELL=bash
CC=yasm
CFLAGS=-f elf64 -m amd64 -Worphan-labels
LD=ld
LDFLAGS=-melf_x86_64

binary={binary}
source={source}
objects=$(source:.asm=.o)

.PHONY: all, debug, release
all: debug

debug: tags
debug: LDFLAGS+=
debug: CFLAGS+=-g dwarf2
debug: $(binary)

release: LDFLAGS+=--strip-all
release: CFLAGS+=
release: $(binary)

$(binary): $(objects)
	$(LD) -o $(binary) $(LDFLAGS) $(objects)

%.o: %.asm
	$(CC) $(CFLAGS) -o $@ $<

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

.PHONY: cleanmake, makeclean
cleanmake makeclean:
	@make --no-print-directory clean && make --no-print-directory;

.PHONY: strip
strip:
	@if strip $(binary); then\
		printf "\n%s was stripped.\n" "$(binary)";\
	else\
		printf "\nError stripping executable: %s\n" "$(binary)" 1>&2;\
	fi;

.PHONY: targets
targets:
	-@printf "Make targets available:\n\
	all       : Build with no optimization or debug symbols.\n\
	clean     : Delete previous build files.\n\
	cleanmake : Run \`make clean && make\`\n\
	makeclean : Alias for \`cleanmake\`\n\
	debug     : Build the executable with debug symbols.\n\
	release   : Build the executable with optimization, and strip it.\n\
	strip     : Run \`strip\` on the executable.\n\
	tags      : Build tags for this project using \`ctags\`.\n\
	";
