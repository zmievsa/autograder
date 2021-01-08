// All non-static functions in student's file are provided by autograder and can be used freely
// PASS(), RESULT(res), FAIL(), and CHECK_STDOUT() are also provided by autograder and can be used freely

// If you want to call a function from student's file in C/C++, you have to prototype it in
// the same way you'd prototype any of your functions.
int some_student_function();

int main()
{
    // You can call any non-static function from student's file like this.
    // It can have any arguments and return values -- use it like any other function.
    some_student_function();

    // If you call this function, the program exits, and then autograder will compare this
    // program's stdout with whatever .txt file (with the same name stem as this test case)
    // you have provided in tests/output directory.
    CHECK_STDOUT();
}