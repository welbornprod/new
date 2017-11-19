# Makefile for {binary}
# {author}{date}
#!
#! Lines starting with #! are not part of the template.
#! New will ignore these lines when processing the template.
#!

SHELL=bash
CXX=g++
CXXFLAGS=-Wall -Wextra -Wfloat-equal -Winline -Wlogical-op \
       -Wmissing-include-dirs -Wnull-dereference -Wpedantic -Wshadow \
       -Wunused-macros -std=c++14
LIBS=

binary={binary}
source={source}
objects={binary}.o

all: $(objects)
	$(CXX) -o $(binary) $(CXXFLAGS) $(objects) $(LIBS)

debug: CXXFLAGS+=-g3 -DDEBUG
debug: all

release: CXXFLAGS+=-O3 -DNDEBUG
release: all
	@if strip $(binary); then\
		printf "\n%s was stripped.\n" "$(binary)";\
	else\
		printf "\nError stripping executable: %s\n" "$(binary)" 1>&2;\
	fi;

$(objects): $(source)
	$(CXX) -c $(source) $(CXXFLAGS) $(LIBS)

.PHONY: clean
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

.PHONY: cleanmake, makeclean
cleanmake makeclean:
	@make --no-print-directory clean && make --no-print-directory;

.PHONY: tags
tags:
	-@printf "Building crags...\n";
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
