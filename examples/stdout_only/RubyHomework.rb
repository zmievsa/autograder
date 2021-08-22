#!/usr/bin/env ruby

def numberSaver()
    arr = Array.new(9, 0)
    sum = 0
    loop do
        puts "Input num from 1 to 9 (0 to exit):\n"
        userInput = gets.chomp.to_i
        if userInput > 0 and userInput < 10
            arr[userInput - 1] += 1
            sum += userInput
        else
            break
        end
    end
    puts "You typed:\n"

    for i in 1..9
        puts "#{i}) #{arr[i-1]} time(s)"
    end

    return sum
end

numberSaver
