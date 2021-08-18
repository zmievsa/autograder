#!/usr/bin/env bash
nums=(0 0 0 0 0 0 0 0 0)
while true
do
	echo "Input num from 1 to 9 (0 to exit): "
	read userInput
	if (($userInput == 0)); then
	  break
	fi
	if (($userInput < 10)); then
	  let userInput-=1
	  ((nums[userInput]++))
	fi
done

echo "You typed:"
for i in {1..9} ; do
  echo "$i) ${nums[(($i-1))]} time(s)"
done

