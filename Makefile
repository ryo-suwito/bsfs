CC = gcc
CFLAGS = -Wall -Wextra -std=c2x -g -O0
LDFLAGS = -lssl -lcrypto -luuid

SRCDIR = .
SOURCES = bsfs.c
OBJECTS = $(SOURCES:.c=.o)
LIBRARY = libbsfs.a
SHARED_LIBRARY = libbsfs.so
TEST_SOURCES = test_bsfs.c
TEST_OBJECTS = $(TEST_SOURCES:.c=.o)
TEST_BINARY = test_bsfs

.PHONY: all clean test shared

all: $(LIBRARY) $(TEST_BINARY)

shared: $(SHARED_LIBRARY)

$(LIBRARY): $(OBJECTS)
	ar rcs $@ $^

$(SHARED_LIBRARY): $(SOURCES)
	$(CC) $(CFLAGS) -fPIC -shared -o $@ $^ $(LDFLAGS)

$(TEST_BINARY): $(TEST_OBJECTS) $(LIBRARY)
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@

test: $(TEST_BINARY)
	./$(TEST_BINARY)

clean:
	rm -f $(OBJECTS) $(TEST_OBJECTS) $(LIBRARY) $(SHARED_LIBRARY) $(TEST_BINARY)
	rm -f *.blob

install: $(LIBRARY) $(SHARED_LIBRARY)
	cp bsfs.h /usr/local/include/
	cp $(LIBRARY) /usr/local/lib/
	cp $(SHARED_LIBRARY) /usr/local/lib/
	ldconfig || true

.PHONY: help
help:
	@echo "Available targets:"
	@echo "  all      - Build static library and test program"
	@echo "  shared   - Build shared library (libbsfs.so)"
	@echo "  test     - Run test suite"
	@echo "  clean    - Remove build artifacts"
	@echo "  install  - Install libraries system-wide"
	@echo ""
	@echo "For Python wrapper:"
	@echo "  make shared  # Build shared library first"
	@echo ""
	@echo "Required packages (Ubuntu/Debian):"
	@echo "  sudo apt-get install libssl-dev uuid-dev"