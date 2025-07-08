#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

int main() {
    printf("Minimal test starting\n");
    
    uint8_t test_array[32];
    memset(test_array, 0, sizeof(test_array));
    
    printf("Array initialized\n");
    
    return 0;
}