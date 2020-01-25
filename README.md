
1) Download student submissions from Webcourses

2) Unzip student submissions into the same directory as "grade-all.sh" (submissions need to be in a
   folder named "submissions")

3) Create your test cases in the same directory as "grade-all.sh"

4) Create a test case sample output .txt file for each of your test cases inside of the "sample_output" folder
	- sample output file names should match the test case they correspond to.

5) Open "grade-all.sh" and edit the following:
	- testcases -> list all grading test case names without file extensions
	- source_file_name -> the name of the source file submitted by students (without extension)
	- total_possible_points -> the total number of grade points allocated for test case results

6) Run "grade-all.sh" from the terminal

7) Rezip the submissions folder and upload the results to Webcourses
