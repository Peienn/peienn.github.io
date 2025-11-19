# Bit manipulate

## 318. Maximum Product of Word Lengths

description: Given a string array words, return the maximum value of length(word[i]) * length(word[j]) where the two words do not share common letters. If no such two words exist, return 0.

Input: words = ["abcw","baz","foo","bar","xtfn","abcdef"] <br>
Output: 16 <br>
Explanation: The two words can be "abcw", "xtfn".

```bash
class Solution(object):
    def maxProduct(self, words):
        """
        :type words: List[str]
        :rtype: int
        """
       
        #計算每一個word的2進制，兩兩進行"AND"，若為0代表無重複
        # "AND"操作
        #  - 兩者為1(同時擁有) --> 1
        #  - 任一為0          --> 0 


        # ex 1:
        # abcw --> 00000000010000000000000111
        # baz  --> 10000000000000000000000011
        # &&------------------------------------
        #          00000000000000000000000011  (has common lettes)

        # ex 2:
        # abcw --> 00000000010000000000000111
        # d    --> 00000000000000000000001000
        # &&------------------------------------
        #          00000000000000000000000000  (no common lettes)  --> check if the maximum


        mask = [0] * len(words)
        # calculate the 2bits format with each word and push in mask
        for i , word in enumerate(words):
            bitmask = 0
            for j in set(word):
                bitmask |= 1<<  (ord(j)-ord('a'))
            mask[i] = bitmask



        # check all pairs if "AND" equals 0
        res = 0
        for i in range(len(words)):
            for j in range(i):
                if mask[i] & mask[j] ==0:
                    res = max(res ,len(words[i]) * len(words[j]))
        return res
```
