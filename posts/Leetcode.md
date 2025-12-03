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

--- 

## 1903. Largest Odd Number in String `(Eazy)`

You are given a string num, representing a large integer. Return the largest-valued odd integer (as a string) that is a non-empty substring of num, or an empty string "" if no odd integer exists.

A substring is a contiguous sequence of characters within a string.

Input: num = "52" <br>
Output: "5" <br>
Explanation: The only non-empty substrings are "5", "2", and "52". "5" is the only odd number.

```bash
class Solution(object):
    def largestOddNumber(self, num):
        """
        :type num: str
        :rtype: str
        """
    

        right = len(num)
        while right > 0 :
            if int(num[right-1]) %2!=0:
                return num[:right]
            else:
                right-=1
            
        return ""
```

從字串中，找出最大(子字串)的奇數。 ex: '53281' 的所有子字串包含:
- 5,3,2,8,1
- 53,32,28,81
- 532,328,281
- 5328,3281
- 53281

想法 : 從個位數開始往前看，只要出現奇數就直接回傳 num[:odd]，不會有比這個還大的奇數。<br>
`因為子字串(Substring)不能亂改順序。`


所以由右到左，只要出現一個奇數，整串就會是最大的奇數。

- '270718`5`2' : 只要出現一個奇數
- '`2707185`2' : 整串就會是最大的奇數

需要考慮中間的  '<u>`27071`</u>852' or  '2<u>`707185`</u>2'嗎 ?  
當然不用，因為一定比整串還要小。

---

# Two Point
## 2161. Partition Array According to Given Pivot `(Medium)`

You are given a 0-indexed integer array nums and an integer pivot. Rearrange nums such that the following conditions are satisfied:

- Every element less than pivot appears before every element greater than pivot.
- Every element equal to pivot appears in between the elements less than and greater than pivot.
- The relative order of the elements less than pivot and the elements greater than pivot is maintained.
    - More formally, consider every pi, pj where pi is the new position of the ith element and pj is the new position of the jth element. If i < j and both elements are smaller (or larger) than pivot, then pi < pj.

Return nums after the rearrangement.

Input: nums = [9,12,5,10,14,3,10], pivot = 10 <br>
Output: [9,5,3,10,10,12,14]<br>
Explanation: 
The elements 9, 5, and 3 are less than the pivot so they are on the left side of the array.
The elements 12 and 14 are greater than the pivot so they are on the right side of the array.
The relative ordering of the elements less than and greater than pivot is also maintained. [9, 5, 3] and [12, 14] are the respective orderings.


解法1:  用雙指標一個從左一個從右
- 如果遇到比pivot小的，就從左邊開始填入(result[left])
- 如果遇到比pivot大的，就從右邊開始填入(result[right])
- 要分兩次是因為要`按照順序`。<br>
 如果在一個loop內 `判斷小就放左，大就放右`，會導致先出現的greater than pivot 在最右邊

```bash
 ex:
 init   : [0,0,0,0,0,0,0] 
 Round1 : [9,0,0,0,0,0,0]
 Round1 : [9,0,0,0,0,0,12]  #Error
```



```bash
#Solution
result = [0] * len(nums)
left = 0
right = len(nums)-1

for i in range(len(nums)):
    if nums[i] < pivot:
        result[left] = nums[i]
        left+=1
    
for j in range(len(nums)-1,-1,-1):
    if nums[j] > pivot:
        result[right] = nums[j]
        right-=1
while left <= right:
    result[left] = pivot
    left+=1

 # First Loop
 init   : [0,0,0,0,0,0,0] 
 Round1 : [9,0,0,0,0,0,0]
 Round2 : [9,0,0,0,0,0,0]  
 Round3 : [9,5,0,0,0,0,0] 
 Round4 : [9,5,0,0,0,0,0] 
 Round5 : [9,5,0,0,0,0,0] 
 Round6 : [9,5,3,0,0,0,0] 
 Round7 : [9,5,3,0,0,0,0] 
 # Second Loop
 init   : [9,5,0,0,0,0,0] 
 Round1 : [9,5,0,0,0,0,0] 
 Round2 : [9,5,0,0,0,0,0] 
 Round3 : [9,5,0,0,0,0,14] 
 Round4 : [9,5,0,0,0,0,14] 
 Round5 : [9,5,0,0,0,0,14] 
 Round6 : [9,5,3,0,0,12,14] 
 Round7 : [9,5,3,0,0,12,14] 
 # 這時候 left = 2 (3) , right = 5 (12)
 # 如果left <=right 代表中間有空格 ，其實就是 pivot的數量
 # 因為比pivot大，比pivot小的都已經填入，剩下的就是等於pivot的
[9,5,3,0,0,12,14] 
[9,5,3,10,10,12,14] 
```

解法2 : 用一個迴圈+兩個stack

按照value的大小各自放入stack , 最後在組裝起來

```bash
less_stack =[] 
great_stack =[]
for i, element in enumerate(nums):
    
    if element < pivot:
        less_stack.append(element)
    elif element > pivot:
        great_stack.append(element)
    
pivot_len = len(nums) - len(less_stack) - len(great_stack) 
result = less_stack + pivot_len * [pivot] + great_stack

# less_stack = [9,5,3]
# great_stack = [12,14]

# pivot_len = 7 - 3 - 2 = 2 (兩個pivot)
# [9,5,3] + [10,10] + [12,14] = [9,5,3,10,10,12,14]

```

# Sliding Window
## 2444. Count Subarrays With Fixed Bounds `(Hard)`

You are given an integer array nums and two integers minK and maxK.

A fixed-bound subarray of nums is a subarray that satisfies the following conditions:

- The minimum value in the subarray is equal to minK.
- The maximum value in the subarray is equal to maxK.

Return the number of fixed-bound subarrays.

A subarray is a contiguous part of an array.

Input: nums = [1,3,5,2,7,5], minK = 1, maxK = 5 <br>
Output: 2 <br>
Explanation: The fixed-bound subarrays are [1,3,5] and [1,3,5,2].

```bash
res = 0
minFound = False
maxFound = False
start = 0
minStart = 0
maxStart = 0
for i in range(len(nums)):
    num = nums[i]
    if num < minK or num > maxK:
        minFound = False
        maxFound = False
        start = i+1
    if num == minK:
        minFound = True
        minStart = i
    if num == maxK:
        maxFound = True
        maxStart = i
    if minFound and maxFound:
        res += (min(minStart, maxStart) - start + 1)

    i+=1

# res
```

說明: 

nums = [2,1,6,-2,7,3,1,4,8,2,6,7,2] minK = 1 maxK = 8

1. 用Sliding Window的方式去找到同時有minK + maxK，`如果還沒同時存在minK + maxK，就遇到範圍外的`，要重新，因為一定組不起來

    - [`2,1,6,-2` ,7,3,1,4,8,2,6,7,2] --> 因為遇到-2 且尚未遇到maxK，重來
    - [2,1,6,-2, `7,3,1,4,8,2,6,7,2`] --> 剩下全部都滿足條件，計算結果

2. 找出計算公式 (min(minStart, maxStart) - start + 1)
    - Base的是 [1,4,8] 當作一個Unit，每增加一個 res就要+1 ex: [3,1,4,8] , [7,3,1,4,8] 
    - 但如果方向不同，每增加一個就要增加另外一邊的倍數
    - 已知 base [1,4,8] 如果只看左邊的話 res = 3 ([7,3,1,4,8] ,[3,1,4,8] , [1,4,8])
    - 現在加入右邊的2 [7,3,1,4,8,`2`]，會直接變成res = 6，因為左邊的三個都可以跟右邊新增的組合成新的 
    -  [7,3,1,4,8] --> [7,3,1,4,8,2]
    - [3,1,4,8] --> [3,1,4,8,2]
    - [1,4,8] --> [1,4,8,2]

於是，公式就會變成

```bash          
                   s      min     max    
[ 2 , 1 , 6 , -2 , 7 , 3 , 1 , 4 , 8 , 2 , 6 , 7 , 2 ]

(min(min,max) - s +1 )

取min是因為不知道是min先出現還是max先出現

[7 , 3 , 1 , 4 , 8] --> res=3
[7 , 3 , 1 , 4 , 8 , 2] --> res=6
[7 , 3 , 1 , 4 , 8 , 2 , 6] --> res=9
...
[7 , 3 , 1 , 4 , 8 , 2 , 6 , 7 , 2 ] --> res=15

# res=15
```


# Array 
## 849. Maximize Distance to Closest Person `(Medium)`
You are given an array representing a row of seats where seats[i] = 1 represents a person sitting in the ith seat, and seats[i] = 0 represents that the ith seat is empty (0-indexed).

There is at least one empty seat, and at least one person sitting.

Alex wants to sit in the seat such that the distance between him and the closest person to him is maximized. 

Return that maximum distance to the closest person.

Input: seats = [1,0,0,0,1,0,1] <br>
Output: 2 <br>
Explanation: <Br>
If Alex sits in the second open seat (i.e. seats[2]), then the closest person has distance 2.
If Alex sits in any other open seat, the closest person has distance 1.
Thus, the maximum distance to the closest person is 2.

```bash
class Solution(object):
    def maxDistToClosest(self, seats):
        """
        :type seats: List[int]
        :rtype: int
        """
    
        l = False
        l_value = 0
        result =0

        for i,element in enumerate(seats):

            if element==0:
                continue
            else:
                if l:
                    # distance between each pair of 1
                    distance = (i-l_value) //2
                    result = max(result , distance)
                else:
                    # distance between [0  , first 1]
                    result = max(result , i-0)
                    l = True
                l_value = i
        # (i-l-value) :  distance between [last 1 , len(seats)]
        return (max( (i-l_value), result))
```

說明 : 

- init : 用`l` 跟 `l_value` 去紀錄目前為止有沒有出現過 1 以及 1 在哪個位置。

- 迴圈去跑 List, 0 的話就跳過不用管，如果找到 1 :
  -  `l` 還沒出現，代表目前是第 1 個 1 ， 要計算這個位置與 0 之間的距離 [`0,0,1`,0,0,1,0,0]  --> i-0
  -  `l` 出現過了，代表目前是第 n 個 1， 要計算與上一個 1 之間的距離並除2 [0,0,`1,0,0,1`,0,0]  -> (i-l_value) //2

- 迴圈結束，在找出最後一個 1 與 尾端的距離 [0,0,1,0,0,`1,0,0`]

- 每次找到的距離都要與 result 取 `max()`。

複雜度 : 

- 時間複雜度 O(n) : 針對len(seats) 執行一次迴圈，且迴圈內每個操作都是O(1)
- 空間複雜度 O(1) : 宣告的變數都是值，沒有任何 List, Dictionary等

---
