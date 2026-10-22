CXX = g++
CXXFLAGS ?= -std=c++20 -O2 -Wall -Wextra
CPPFLAGS += -Icommon/src
PYTHON ?= python3

LABS := lab1 lab2 lab3 lab4 lab5 lab6 lab7 lab8 lab9 lab10 lab11 lab12
COMMON_SOURCES := $(wildcard common/src/*.cpp)
COMMON_HEADERS := $(wildcard common/src/*.hpp)

.PHONY: all
all: $(foreach lab,$(LABS),$(if $(wildcard $(lab)/src/*.cpp),$(lab)))

define LAB_RULES
.PHONY: $(1) run-$(1) visualize-$(1)

$(1): $(1)/out/main

$(1)/out/main: $(wildcard $(1)/src/*.cpp) $(wildcard $(1)/src/*.hpp) $(COMMON_SOURCES) $(COMMON_HEADERS) Makefile
	@test -n "$(wildcard $(1)/src/*.cpp)" || { echo "Brak plikĂłw C++ w $(1)/src"; exit 1; }
	mkdir -p $(1)/out
	$$(CXX) $$(CPPFLAGS) $$(CXXFLAGS) $$(filter %.cpp,$$^) -o $$@

run-$(1): $(1)
	./$(1)/out/main

visualize-$(1):
	$$(PYTHON) common/src/visualize_experiments.py $(1)
endef

$(foreach lab,$(LABS),$(eval $(call LAB_RULES,$(lab))))

# Reuse construction heuristics without linking lab2's main or experiment runner.
lab3/out/main: lab2/src/lab2_methods.cpp lab2/src/lab2_methods.hpp common/src/utils.hpp
lab3/out/main: CPPFLAGS += -Ilab2/src
