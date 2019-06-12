# Makefile for {binary}
# {author}{date}
#!
#! Lines starting with #! are not part of the template.
#! New will ignore these lines when processing the template.
#!

SHELL=bash
CC=cargo
dir_debug=$(CURDIR)/target/debug
dir_release=$(CURDIR)/target/release
source={source_path}

.PHONY: all, debug

all: $(source)
	$(CC) build --release;

debug: $(source)
	$(CC) build;

.PHONY: run
run:
	$(CC) run --release;
	-@echo -e "\n\n...just use \`cargo run\`.";

.PHONY: clean
clean:
	cargo clean;

.PHONY: help, targets
help targets:
	-@printf "Make targets available:\n\
	all        : Build a release executable.\n\
	clean      : Remove the ./target directory.\n\
	cleanmake  : Runs \`make clean && make\`.\n\
	debug      : Build a debug executable.\n\
	makeclean  : Alias for \`cleanmake\`  target.\n\
	run        : Run the release executable, build if needed.\n\
	";
