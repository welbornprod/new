# Makefile for {binary}
# {author}{date}

SHELL=bash
CC=nasm
LD=ld
CFLAGS=-felf64 -Wall
LDFLAGS=-O1

binary={binary}
source={source}
objects={binary}.o

all: $(objects)
	$(LD) -o $(binary) $(LDFLAGS) $(objects)

debug: LDFLAGS+=
debug: CFLAGS+=-F stabs -g
debug: all

release: LDFLAGS+=--strip-all
release: CFLAGS+=-Ox
release: all
	@if strip $(binary); then\
		printf "\n%s was stripped.\n" "$(binary)";\
	else\
		printf "\nError stripping executable: %s\n" "$(binary)" 1>&2;\
	fi;

$(objects): $(source)
	$(CC) $(CFLAGS) $(source)

.PHONY: clean, cleanmake, makeclean, targets
clean:
	-@if [[ -e $(binary) ]]; then\
		if rm -f $(binary); then\
			printf "Binaries cleaned.\n";\
		fi;\
	else\
		printf "Binaries already clean.\n";\
	fi;

	-@if ls *.o &>/dev/null; then\
		if rm *.o; then\
			printf "Objects cleaned.\n";\
		fi;\
	else\
		printf "Objects already clean.\n";\
	fi;


cleanmake makeclean:
	@make --no-print-directory clean && make --no-print-directory;

targets:
	-@printf "Make targets available:\n\
	all       : Build with no optimization or debug symbols.\n\
	clean     : Delete previous build files.\n\
	cleanmake : Run \`make clean && make\`\n\
	makeclean : Alias for \`cleanmake\`\n\
	debug     : Build the executable with debug symbols.\n\
	release   : Build the executable with optimization, and strip it.\n\
	";

