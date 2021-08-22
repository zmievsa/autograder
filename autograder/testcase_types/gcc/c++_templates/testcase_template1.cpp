// All non-static functions in student's file are provided by autograder and can be used freely
// PASS(), RESULT(res), FAIL(), and CHECK_STDOUT() are also provided by autograder and can be used freely

// If you want to call a function from student's file in C/C++, you have to prototype it in the same way you'd prototype any of your functions.
int some_student_function();

int main()
{
    // You can call any non-static function from student's file like this.
    // It can have any arguments and return values -- use it like any other function.
    int result = some_student_function();

    int SOME_EXPECTED_RESULT = 83;
    if (result == SOME_EXPECTED_RESULT)
        PASS();
    else
        FAIL();
}