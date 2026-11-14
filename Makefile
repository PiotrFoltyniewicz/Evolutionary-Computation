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

# Reuse local search without linking lab3's main or experiment runner.
lab4/out/main: lab3/src/local_search_methods.cpp lab3/src/local_search_methods.hpp
lab4/out/main: CPPFLAGS += -Ilab3/src

# Lab 5 uses the same full-neighborhood baseline as lab 3.
lab5/out/main: lab3/src/local_search_methods.cpp lab3/src/local_search_methods.hpp
lab5/out/main: CPPFLAGS += -Ilab3/src

.PHONY: test-lab5
test-lab5: lab5/out/move_list_search_test
	./lab5/out/move_list_search_test

lab5/out/move_list_search_test: lab5/tests/move_list_search_test.cpp lab5/src/move_list_search.cpp lab5/src/move_list_search.hpp lab3/src/local_search_methods.cpp lab3/src/local_search_methods.hpp $(COMMON_SOURCES) $(COMMON_HEADERS)
	mkdir -p lab5/out
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) -Ilab3/src lab5/tests/move_list_search_test.cpp lab3/src/local_search_methods.cpp $(COMMON_SOURCES) -o $@

# Lab 6 reuses the move-list LS from lab 5.
lab6/out/main: lab5/src/move_list_search.cpp lab5/src/move_list_search.hpp
lab6/out/main: CPPFLAGS += -Ilab5/src
