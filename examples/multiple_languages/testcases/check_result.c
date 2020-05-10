int add(int a, int b);


int main() {
    int result = add(1, 2);
    if (result == 3)
        PASS();
    else
        FAIL();
}
