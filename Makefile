CXX = g++
CXXFLAGS ?= -std=c++20 -O2 -Wall -Wextra
CPPFLAGS += -Icommon/src

LAB1_SOURCES := $(wildcard lab1/src/*.cpp) $(wildcard common/src/*.cpp)
LAB1_HEADERS := $(wildcard lab1/src/*.hpp) $(wildcard common/src/*.hpp)

.PHONY: all lab1 run-lab1 visualize-lab1
all: lab1

lab1: lab1/out/main

lab1/out/main: $(LAB1_SOURCES) $(LAB1_HEADERS) Makefile
	mkdir -p lab1/out
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) $(LAB1_SOURCES) -o $@

run-lab1: lab1
	./lab1/out/main

visualize-lab1:
	python3 lab1/src/visualize_experiments.py
