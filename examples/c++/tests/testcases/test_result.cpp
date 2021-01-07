// All non-static functions in student's file are provided by autograder and can be used freely if you prototype them below.
// PASS(), RESULT(res), FAIL(), and CHECK_OUTPUT() are also provided by autograder

int numberSaver();

int main()
{
    int res = numberSaver(); // You can call any non-static function from student's file like this
    if (res == 54)
        PASS();
    else
        FAIL();
}