testcases=(
	"ExampleTestCase"
)

source_file_name="ExampleAssignment"
assignment_name="Example"
total_possible_points=60

earned_points=0
num_students=0

rm -f *.class
rm -f $source_file_name.java
rm -f output.txt

for filename in ./submissions/*$source_file_name*.java;
do
	# Get the student's name from the filename
	name=${filename%_*}
	name=${name%_*}
	name=${name%_*}
	name=${name##*/}

	printf "Grading: ${name}... "

	# Copy the source code into the testing folder
	cp "$filename" $source_file_name.java

	# Remove the old source files from the submissions folder -> they will be replaced with results
	rm -f "$filename"

	num_cases=0
	num_pass=0

	echo "$assignment_name Test Results" >> "$filename"

	printf "\n%17s%28s\n" "TestCase" "Result" >> "$filename"
	echo "================================================================" >> "$filename"

	# Run the test cases and write the results to the original file in the submissions folder
	for testcase in ${testcases[@]};
	do
		((num_cases++))
		printf %-34s $testcase.java >> "$filename"

		rm -f *.class
		rm -f output.txt

		# Check if the test case compiles
		javac $testcase.java 2> /dev/null
		compile_value=$?
		if [ $compile_value != 0 ]; then
			echo "Failed to Compile!" >> "$filename"
			continue
		fi

		rm -f *.class

		# Check if the test case throws warning messages
		javac -Werror $testcase.java -Xlint:unchecked 2> /dev/null
		compile_value=$?
		if [ $compile_value != 0 ]; then
			printf "Compiled with warnings! - " >> "$filename"
			#printf "\n" >> "$filename"
			#continue
		fi

		# Check if the test case crashes
		timeout 60 java $testcase > output.txt 2> /dev/null
		runtime_value=$?
		if [ $runtime_value == 124 ]; then
			echo "Exceeded Time Limit!" >> "$filename"
			continue
		elif [ $runtime_value != 0 ]; then
			echo "Crashed!" >> "$filename"
			continue
		fi

		# Check if the output is correct
		diff output.txt sample_output/$testcase.txt > /dev/null 2> /dev/null
		diff_value=$?
		if [ $diff_value != 0 ]; then
			echo "Wrong Answer!" >> "$filename"
			continue
		fi

		echo "PASS" >> "$filename"
		((num_pass++))
	done

	let num_pass=($num_pass * $total_possible_points / $num_cases)
	echo "Done. $num_pass/$total_possible_points"

	echo "================================================================" >> "$filename"
	echo  >> "$filename"
	echo "Result: $num_pass/$total_possible_points" >> "$filename"

	printf "\nKey:\n" >> "$filename"
	printf "\tPASS: Your Submission is awesome\n" >> "$filename"
	printf "\tFailed to Compile!: Your submission did not compile due to a syntax or naming error\n" >> "$filename"
	printf "\tCompiled with warnings!: Your submission uses unchecked or unsafe operations\n" >> "$filename"
	printf "\tCrashed!: Your submission threw an uncaught exception\n" >> "$filename"
	printf "\tExceeded Time Limit!: Your submission took longer than 60 seconds to run (probably an infinite loop)\n" >> "$filename"
	printf "\tWrong Answer!: Your submission produced the wrong result or generated too much output\n" >> "$filename"
	echo >> "$filename"

	# Clean up
	rm -f *.class
	rm -f $source_file_name.java
	rm -f output.txt

	let earned_points=($earned_points + $num_pass)
	((num_students++))

done

let average=($earned_points / $num_students)
echo
echo "Average score: $average/$total_possible_points"
