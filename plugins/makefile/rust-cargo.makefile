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


.PHONY: all
all:
	$(CC) build --release;

.PHONY: debug
debug:
	$(CC) build;

.PHONY: run
run:
	$(CC) run --release;
	-@echo -e "\n\n...just use \`cargo run\`.";

.PHONY: clean
clean:
	cargo clean;

.PHONY: cleanmake, makeclean
cleanmake makeclean:
	@make --no-print-directory clean && make --no-print-directory;

.PHONY help
help:
	-@printf "Use 'make targets' for a list of available targets.\n";

.PHONY: targets
targets:
	-@printf "Make targets available:\n\
	all        : Build a release executable.\n\
	clean      : Remove the ./target directory.\n\
	cleanmake  : Runs \`make clean && make\`.\n\
	debug      : Build a debug executable.\n\
	makeclean  : Alias for \`cleanmake\`  target.\n\
	run        : Run the release executable, build if needed.\n\
	targets    : Show this message.\n\
	";
