#include <vector>
#include <string>
#include <memory>
#include <cstring>

class Test {
    public:
        Test(const std::string& hello) : _hello(hello){}
    private:
        std::string _hello;
};

char * string_to_char(const std::string& str){
    char * cstr = new char [str.length()+1];
    std::strcpy (cstr, str.c_str());
    return cstr;
}

int main(void) {
    /* Creating Vectors */
    std::vector<int> vec_int(0); // 0 allocation
    vec_int.push_back(1);        // 1 allocation
    vec_int.push_back(1);        // 1 allocation
    vec_int.push_back(1);        // 1 allocation

    std::vector<double> vec_double(3,1.0); // 1 allocation

    Test simple("hi there !"); // 0 allocation

    std::unique_ptr<Test> hello(new Simple("apple")); // 1 allocation

    /* raw pointer */
    const std::string arg = "hello";        // 0 allocation
    char * arg_char = string_to_char(arg);  // 1 allocation
    Test * _hello = new Test(arg_char); // 1 allocation

    delete arg_char;
    (void)_hello;
    
    // do not free: delete _hello;

    return EXIT_SUCCESS;
}
