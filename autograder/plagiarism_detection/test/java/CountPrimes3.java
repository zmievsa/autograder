public class CountPrimes3 {
    public int countPrimes(int n) {
        boolean[] primes = new boolean[n+1];
        int count = 0;
        Arrays.fill(primes, true);
        for(int i = 2; i <= Math.sqrt(n); i++)
        {
            if(primes[i])
            {
                count++;
                for(int j = i*2; j < n; j = j + i)
                {
                    primes[j] = false;
                }
            }
        }
        for(int k = (int)(Math.sqrt(n))+1; i < n; i++)
        {
            if(primes[i]) {
                count++;
            }
        }
        return count;
    }
}