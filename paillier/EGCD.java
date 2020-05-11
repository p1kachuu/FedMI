/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */
package thresholdEnc;
import java.math.BigInteger;
/**
 *
 * @author xmliu
 */
public class EGCD {
     /**
         * Performs Euclids GCD algorithm
         * 
         * @param a
         * @param b
         * @return
         */
        public static BigInteger Euclidean(BigInteger a, BigInteger b)
        {
                if (b.compareTo(BigInteger.ZERO) == 0)
                        return a;
                
                return Euclidean(b, a.mod(b));
        }
        
        /**
         * Performs the Extended Euclidean algorithm to calculate the GCD
         * as well as the modular inverses.
         * 
         * @param a
         * @param b
         * @return
         */
        public static BigInteger[] ExtEuclidean(BigInteger a, BigInteger b)
        {
                /*
                 * res[0] = x
                 * res[1] = y
                 * res[2] = d
                 * ax + by = d = gcd(a, b)
                 */
                BigInteger[] res = new BigInteger[3];
                
                if (b.compareTo(BigInteger.ZERO) == 0) {
                        res[0] = BigInteger.ONE;
                        res[1] = BigInteger.ZERO;
                        res[2] = a;
                }
                else {
                        BigInteger[] temp = ExtEuclidean(b, a.mod(b));
                        res[0] = temp[1];
                        res[1] = temp[0].subtract(temp[1].multiply(a.divide(b)));
                        res[2] = temp[2];
                }
                
                return res;
}
        
               
}
