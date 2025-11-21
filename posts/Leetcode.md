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
---


# String
## 3210. Find the Encrypted String `(Eazy) (One Line)`

You are given a string s and an integer k. Encrypt the string using the following algorithm:

- For each character c in s, replace c with the kth character after c in the string (in a cyclic manner).

Return the encrypted string.

Input: s = "dart", k = 3

Output: "tdar"

Explanation:

For i = 0, the 3rd character after 'd' is 't'. <br>
For i = 1, the 3rd character after 'a' is 'd'.<br>
For i = 2, the 3rd character after 'r' is 'a'.<br>
For i = 3, the 3rd character after 't' is 'r'.<br>

```bash
class Solution(object):
    def getEncryptedString(self, s, k):
        """
        :type s: str
        :type k: int
        :rtype: str
        """
        return (s+s)[k%len(s): (k%len(s)+len(s))]
```

1. 位移最多是從第1個字符轉到最後一個，使用 s + s 可以涵蓋所有旋轉組合。
2. 位移超過字串長度時，取餘數處理，例如 k % len(s)。 因為"abc" 位移3次結果等同未移動。

案例:

s = abcde , k = 3  
1. abcdeabcde (s+s)
2. 從第三個開始取到字串長度 = s[3%5:3%5+5] = s[3:3+5] = s[3:8] = abc`deabc`de = deabc

s = abcde , k = 14
1. abcdeabcde (s+s)
2. 因為 k > 字串長度 = s[13%5:13%5+5] = s[3:8] = abc`deabc`de = deabc
