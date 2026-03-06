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

## 67. Add Binary `(Eazy)`

Given two binary strings a and b, return their sum as a binary string.

Example 1:

Input: a = "11", b = "1" <br>
Output: "100"

### Solution 1:

```bash
class Solution(object):
    def addBinary(self, a, b):
        """
        :type a: str
        :type b: str
        :rtype: str
        """
        def binaryToInt(string):
            
            result = 0
            for i in range(len(string)-1 , -1 ,-1):
                result +=  2**  (len(string)-1-i) * int(string[i])
            return result

        def IntToBinary(integer):
                
            if integer==0:
                return '0'

            result=""
            while integer>0:
                result = str(integer %2) + result
                integer//=2
            
            return result
        
        return IntToBinary( binaryToInt(a) + binaryToInt(b))
```

說明 : 

這個方法主要是寫兩個 function，一個是將binary String 轉 Integer，另一個是將 Integer 轉回去 binary string。

所以就只要將兩個 binary string 都轉成 Integer 後相加，再轉回去 binary string 即可。

### Solution 2

```bash
class Solution(object):
    def addBinary(self, a, b):
        """
        :type a: str
        :type b: str
        :rtype: str
        """
        res = ""
        i, j, carry = len(a) - 1, len(b) - 1, 0
        while i >= 0 or j >= 0:
            sum = carry
            if i >= 0 : sum += ord(a[i]) - ord('0') 
            if j >= 0 : sum += ord(b[j]) - ord('0')
            i, j = i - 1, j - 1
            carry = 1 if sum > 1 else 0
            res = str(sum % 2) + res
            
        if carry != 0 : res = str(carry)+res;

        return res
```
說明 :

1. 用 carry 去 Keep 住要不要進位
2. 用 sum 去計算相加後是多少 (還要加上 carry)，並判斷下一輪的 carry 以及這一輪的餘數

Ex:  a = "11", b = "1"

- init: carry=0, a=1, b=0
- Loop1: sum=0, `ord(a[i]) - ord('0')=1`, `ord(b[j]) - ord('0')=1`, 所以 sum=2。 因為 sum >1 所以要進位，carry = 1 , 這一輪的餘數就是 sum%2  
- 如果最後結束 carry ==1 , 代表最後一輪還有進位，要補上去

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


## 1658. Minimum Operations to Reduce X to Zero `(Medium)`
You are given an integer array nums and an integer x. In one operation, you can either remove the leftmost or the rightmost element from the array nums and subtract its value from x. Note that this modifies the array for future operations.

Return the minimum number of operations to reduce x to exactly 0 if it is possible, otherwise, return -1.

Input: nums = [3,2,20,1,1,3], x = 10 <br>
Output: 5 <br>
Explanation: The optimal solution is to remove the last three elements and the first two elements (5 operations in total) to reduce x to zero.

```bash
class Solution(object):
    def minOperations(self, nums, x):
        
        target = sum(nums)-x

        if target ==0:
            return len(nums)
        
        # the sum of all the elements is less than "x"
        if target <0:
            return -1

        
        left = 0
        curr_sum = 0
        result = 0
        for right in range(len(nums)):

            curr_sum += nums[right]
            while curr_sum > target and left<=right:
                curr_sum -= nums[left]
                left+=1

            if curr_sum ==target:
                result = max(result , right-left+1)
            
        return  len(nums) - result if result else -1
```

說明 :

透過Sliding Windows的方式，去檢查目前 Windows 內的值總和是不是我們要的差額 (差額 = "所有總和-x" )

如果是的話，用 len(nums) - len( Windows) ， 這個長度就是 "剩餘所有值相加 = 10"

舉例來說: nums = [3, 2, 20, 1, 1, 3] , x = 10

1. target = 30 - 10 = 20

2. 當我們 滑動 Windows 到裡面只剩下 [`20`] 時， 剩餘的數字加總就會是 "x"  [`3, 2` , 20 , `1, 1, 3` ]

3. 這時用 len(nums) - len(windows) = 6 - 1 = 5 

4. 代表我們總共需要 5 個值 才可以組成 x  (也就是 3, 2, 1, 1, 3)


當然，上述標準解法。

---

我個人一開始的想法:

題目表示可以從左邊或右邊去尋找加總的值，但因為不知道要從左邊還是右邊。因此第一想法是透過BFS，找出所有路徑，只要遇到加總為 x 就 return。

舉上面的案例來說: queue放入初始值 左1  跟 右1

左1 : 下一步可以走 左2 或是 左1 + 右1
右1 : 下一步可以走 左1+右1 或是 右2

以此類推，這樣就可以從兩邊開始往中間推進，直到找出 sum 為 x 的 list。但這樣做的時間複雜度太高，都是TLE。

但當我看到標準解法後才想到， `Sliding Windows內的值如果是 "差額"，那剩餘的值不就該好也是從左邊跟右邊加總而來`， 那我就不需要思考下一步到底要從左邊開始走，還是從右邊開始走。


下面是BFS的解法，在Leetcode上跑到 73 Case就TLE

```bash
n =  len(nums)
       
queue = deque()        
visited = set()

queue.append( (1, n , nums[0] , 1))
queue.append( (0,n-1,nums[n-1],1))
visited.add( (1, n , nums[0]) )
visited.add((0, n-1, nums[-1]))

while queue:
    
    curr_l , curr_r , curr_sum, step = queue.popleft()
    
    if curr_sum ==x:
        return step
    if curr_sum >x:
        continue
    
    if curr_l +1 < curr_r:
        next_sum = curr_sum + nums[curr_l]
        state = (curr_l+1 , curr_r , next_sum)
        if state not in visited:
            visited.add(state)
            queue.append( (curr_l+1,curr_r,next_sum , step+1))

    if curr_l <= curr_r-1:
        next_sum = curr_sum + nums[curr_r-1]
        state = (curr_l , curr_r-1, next_sum)
        if state not in visited:
            visited.add(state)
            queue.append((curr_l,curr_r-1, next_sum ,step+1))
                  
return -1
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

## 80. Remove Duplicates from Sorted Array II  `(Medium)`

Given an integer array nums sorted in non-decreasing order, remove some duplicates in-place such that each unique element appears at most twice. The relative order of the elements should be kept the same.

Since it is impossible to change the length of the array in some languages, you must instead have the result be placed in the first part of the array nums. More formally, if there are k elements after removing the duplicates, then the first k elements of nums should hold the final result. It does not matter what you leave beyond the first k elements.

Return k after placing the final result in the first k slots of nums.

Do not allocate extra space for another array. You must do this by modifying the input array in-place with O(1) extra memory.

**Custom Judge:**

The judge will test your solution with the following code:
```
int[] nums = [...]; // Input array
int[] expectedNums = [...]; // The expected answer with correct length

int k = removeDuplicates(nums); // Calls your implementation

assert k == expectedNums.length;
for (int i = 0; i < k; i++) {
    assert nums[i] == expectedNums[i];
}
```

If all assertions pass, then your solution will be accepted.

Example 1:

Input: nums = [1,1,1,2,2,3] <br>
Output: 5, nums = [1,1,2,2,3,_]  <br>
Explanation: Your function should return k = 5, with the first five elements of nums being 1, 1, 2, 2 and 3 respectively.It does not matter what you leave beyond the returned k (hence they are underscores).

```bash
# Code
class Solution(object):
    def removeDuplicates(self, nums):
        """
        :type nums: List[int]
        :rtype: int
        """
        current = nums[-1]
        number=1
        for i in range(len(nums)-2 , -1 ,-1):
            
            if nums[i]==current:
                
                if 2> number:
                    number+=1
                else:
                    nums.pop(i)
            else:
                current = nums[i]
                number=1
```

說明 :

題目要求把重複超過兩次的數字給移除，且不能用額外的空間。最後找出還有幾個數字存在。

方法主要就是從最後面開始，如果遇到重複的數字就 number +1 ， number 如果超過2 就 pop()出去。
用 current 去 keep 當前的數字是多少。

```bash
# Others Solution
class Solution:
    def removeDuplicates(self, nums: List[int]) -> int:
        j = 1
        for i in range(1, len(nums)):
            if j == 1 or nums[i] != nums[j - 2]:
                nums[j] = nums[i]
                j += 1
        return j
```
說明 :

一種經典解法，用 J 來 Keep 住` 哪個位置要被置換`

1. j == 1 是為了讓陣列的前兩個元素能直接保留，初始化時就支持兩個元素。那為甚麼不要直接 `j=2 + for i in range(2,len(nums))` ? 因為這樣在 陣列長度等於 1 時會出錯。

2. nums[i] != nums[j-2] 是用來判斷目前掃描到的元素，是否與`結果陣列`中倒數第二個元素不同

3. 舉例 : 因為初始化  j=1 + if (j==1)，會直接讓 j=2,


    - 首先，我們在 j 以前的都是結果陣列，也就是正確的答案 [`1, 1` , 1 , 2, 2, 3] 
    - 當 i=2, j=2 時出現第三個 1，此時 j 不動，i 繼續往下。 因為 nums[i] 跟結果陣列中的倒數第二個一致，代表連續出現三個。而 j 是為了 Keep 住哪個位置要被置換，所以不能走
    - i=3 , j=2 時出現 2 ，與結果陣列的倒數第二個不同，因此把 j 換成 nums[i]
    - [1, 1 , `1` , 2, 2, 3]  -->  [1, 1 , `2` , 2, 2, 3] ，以此類推往下


#### 過程

| Step | i 指向元素 | 判斷條件 (j == 1 or nums[i] != nums[j-2]) | 動作 (寫入 & 移動 j)      | nums狀態                   | j 位置 |
|-------|------------|-------------------------------------------|---------------------------|----------------------------|---------|
| init     | -          | -                                         | 初始化 j = 1               | [1, 1, 1, 2, 2, 3]         | 1       |
| 1     | 1 (nums[1]=1) | j==1 (True)                           | nums[1] = 1，j → 2        | [1, 1, 1, 2, 2, 3]         | 2       |
| 2     | 2 (nums[2]=1) | nums[2] == nums[0] → 1 == 1 (False) | **跳過**                   | [1, 1, 1, 2, 2, 3]         | 2       |
| 3     | 3 (nums[3]=2) | 2 != nums[0] (1) (True)              | nums[2] = 2，j → 3        | [1, 1, 2, 2, 2, 3]         | 3       |
| 4     | 4 (nums[4]=2) | 2 != nums[1] (1) (True)              | nums[3] = 2，j → 4        | [1, 1, 2, 2, 2, 3]         | 4       |
| 5     | 5 (nums[5]=3) | 3 != nums[2] (2) (True)              | nums[4] = 3，j → 5        | [1, 1, 2, 2, 3, 3]         | 5       |


---

## 73. Set Matrix Zeroes  `(Medium)`

Given an m x n integer matrix matrix, if an element is 0, set its entire row and column to 0's.

You must do it in place.


Input: matrix = [[1,1,1],[1,0,1],[1,1,1]]

Output: [[1,0,1],[0,0,0],[1,0,1]]


說明 : 因為必須 in place 替換，為避免被 `替換的 0 ` 被當作`初始的 0 `，所以先找出所有`初始 0 ` 的位置，再依序的根據每個`初始 0` 的座標去置換。
```bash
class Solution(object):
    def setZeroes(self, matrix):
        """
        :type matrix: List[List[int]]
        :rtype: None Do not return anything, modify matrix in-place instead.
        """
        rows = len(matrix)

        cols = len(matrix[0]) 

        count_row=[]
        count_col=[]
        for row in range(rows):
            
            for col in range(cols):
                
                if matrix[row][col] == 0:
                    
                    count_row.append(row)
                    count_col.append(col)
                    

        for i in count_row:
            matrix[i] = [0] * len(matrix[0])
            
            

        for i in count_col:
            
            for row in matrix: row[i] = 0
            
```

---



# BFS

## 1654. Minimum Jumps to Reach Home `(Medium)`

A certain bug's home is on the x-axis at position x. Help them get there from position 0.

The bug jumps according to the following rules:

- It can jump exactly a positions forward (to the right).
- It can jump exactly b positions backward (to the left).
- It cannot jump backward twice in a row.
- It cannot jump to any forbidden positions.
The bug may jump forward beyond its home, but it cannot jump to positions numbered with negative integers.

Given an array of integers forbidden, where forbidden[i] means that the bug cannot jump to the position forbidden[i], and integers a, b, and x, return the minimum number of jumps needed for the bug to reach its home. If there is no possible sequence of jumps that lands the bug on position x, return -1.


Example 1:

Input: forbidden = [14,4,18,1,15], a = 3, b = 15, x = 9 <br>
Output: 3 <br>
Explanation: 3 jumps forward (0 -> 3 -> 6 -> 9) will get the bug home.

```bash
class Solution(object):
    def minimumJumps(self, forbidden, a, b, x):
        """
        :type forbidden: List[int]
        :type a: int
        :type b: int
        :type x: int
        :rtype: int
        """
        upper_bound =  max(forbidden)+a+b+x

        # BFS
        visited = set()
        visited.add((0,False))
        queue = deque([(0,False)])

        result = 0
        while queue:

            for _ in range(len(queue)):

                position , lastIsBack = queue.popleft()

                if position==x:
                    return result
                
                #  go Forward
                next_position = position + a

                if (0<=next_position<=upper_bound)  and (next_position not in forbidden) and ( (next_position , False) not in visited):
                    visited.add((next_position , False))
                    queue.append((next_position, False))

                #  go Backward
                next_position = position - b
                if (not lastIsBack) and (0<=next_position<=upper_bound)  and (next_position not in forbidden) and ( (next_position , True) not in visited):

                    visited.add((next_position , True))
                    queue.append((next_position, True))
                
            # every round need to add 1 
            result +=1
        
        return -1
```

說明 : 簡單來說就是從 0 到 x ，往前一步 = a , 往後一步 = b , 不能連續後退兩步。試問 0 到 x 最短距離要幾步? 如果無法到達回傳 -1


這題透過BFS，將`每次可以到達的index 存在Queue內`，`同時記錄這一步是不是後退步`。如果這一回合走完都沒有到達 x 的話，距離要+1，直到結束。



ex: forbidden = [5,10,14,18,23], a = 7, b = 3, x =19

- init : queue = 0 , False
- round 1 : queue = (7, False)   因為只能往前走 a = 7
- round 2 : queue =  (4, True)  7如果往前走變成 (14,False) 採到forbidden所以不能紀錄  
- round 3 : queue = (11, False) 因為上一步是後退，這一次只能往前走 4+7=11
- round 4 : queue = (8, True)  11+7採到forbidden
- round 5 : queue = (15, False)  只能前進
- round 6 : queue = [ (22, False) , (12, True)]
- round 7 : queue 
    1. POP (22, False)
    2. 加入 (2, False)到Queue
    3. 準備加入 (19, True)到Queue時發現， 19 ==x ，直接return 7。


---


# Dynamic Programming

## 139. Word Break `(Medium)`

Given a string s and a dictionary of strings wordDict, return true if s can be segmented into a space-separated sequence of one or more dictionary words.

Note that the same word in the dictionary may be reused multiple times in the segmentation.

Example 1:

Input: s = "leetcode", wordDict = ["leet","code"] <br>
Output: true <br>
Explanation: Return true because "leetcode" can be segmented as "leet code".

```bash
class Solution(object):
    def wordBreak(self, s, wordDict):
        """
        :type s: str
        :type wordDict: List[str]
        :rtype: bool
        """

        dp = [False] * ((len(s)+1))

        dp[0]=True

        for i in range(1 , len(dp)):

            for j in range(i):

                if dp[j] and s[j:i] in wordDict:
                    dp[i]=True
                    break

        return dp[-1]
```

說明 : 

dp[j]
- 若為True  代表 dp[:j] 是可以被 wordDict 內的單詞組合而成 <br>
    
- 若為False 代表 dp[0:j] , dp[1:j] ... dp[j-1:j] 都是無法被Dict組成


if dp[j] and s[j:i] in wordDict 的判斷意思為:
    
- 如果 dp[j]是可以被Dict 單詞給組成，  且 s[j:i] (剩餘的string)也 存在於wordDict  <br>
  -> 整個string都可以被 wordDict組成

Ex: s= 'leetcode', wordDict = ['leet', 'code']
1. (init)  dp =  [T, F, F, F, F, F, F, F, F]
2.  l, le, lee 都不存在於 wordDict ，所以 dp =  [T, F, F, F, F, F, F, F, F]
3.  i = 4 ; j=0 時， `dp[0] default=True` + `s[0:4] in wordDict` 因此 dp[4] 設 True，<br> 同時也代表 s[0:4] = leet 存在 wordDict 。
4. 依序直到最後 dp = [T, F, F, F, T, F, F, F, F] ，i = 8 時
5. j=0 ~ j=3 因為 dp[j]==False 代表 l, le, lee 都不存在於 wordDict。而 j=4 時發現 dp[4]=  True，代表 dp[0:4] = 'leet' 有在 wordDict，因此再判斷 s[4:8]='code' 有無 in wordDict，因為 'code' 存在 worDict 因此將 dp[i]=dp[8] 設為 True。

6. 最後，檢查最後一個字母 dp[-1] 能不能被組成即可，也就是說 dp[-1]==True。


---

## 198. House Robber `(Medium)`


You are a professional robber planning to rob houses along a street. Each house has a certain amount of money stashed, the only constraint stopping you from robbing each of them is that adjacent houses have security systems connected and it will automatically contact the police if two adjacent houses were broken into on the same night.

Given an integer array nums representing the amount of money of each house, return the maximum amount of money you can rob tonight without alerting the police.


Example 1:

Input: nums = [1,2,3,1] <br>
Output: 4  <br>
Explanation: Rob house 1 (money = 1) and then rob house 3 (money = 3).
Total amount you can rob = 1 + 3 = 4.

```bash
class Solution(object):
    def rob(self, nums):
        """
        :type nums: List[int]
        :rtype: int
        """
        
        dp = [0] * (len(nums)+1)
        dp[1] = nums[0]

        for i in range(2 , len(nums)+1):
            
            dp[i] = max(dp[i-1] , dp[i-2]+nums[i-1])
            

        return dp[-1]

```

說明 : 

算是蠻標準的 DP 題目，可以透過儲存每一個位置的最大值，來推斷最後的最大值。

每一格的最大值可能是 `前一格` or `前兩格 + 自己` ，為甚麼不會是前三格前四格? 因為這些都會被包含前一格或前兩格。 

- 如果你要考慮前三格，為何不選擇前三格 + 前一格? 而前一格的嘉總值一定大於前三格。 

- 如果你要考慮前四格? 為何不選擇前四格 + 前兩格。同理，前兩格一定大於前四格

EX: nums [1,2,3,1]

1. (init) dp=[0,1,0,0,0] ; 
2.  i=2 ，我們計算 dp[2] 的時候，上一次只會是從前兩格來的。或是上一次是選前一格而這一次不選。<br>因此 dp[2] = max( dp[2-1] , dp[2-2]+ nums[2] ) 。 dp=[0,1,2,0,0]

3. i=3 同理， dp[3] = max( dp[3-1] , dp[3-2]+ nums[3]) 。 dp=[0,1,2,4,0]
4. i=4 同理， dp[4] = max( dp[4-1] , dp[4-2]+ nums[4]) 。 dp=[0,1,2,4,4]。

最後，我們知道走到最後最大值是 4 ，而且可以 `往回推論出` 是從 3 --> 1 加總而來。

---

# Stack (implemented using list)

## 150. Evaluate Reverse Polish Notation `(Medium)`

You are given an array of strings tokens that represents an arithmetic expression in a Reverse Polish Notation.

Evaluate the expression. Return an integer that represents the value of the expression.

Note that:

- The valid operators are '+', '-', '*', and '/'.
- Each operand may be an integer or another expression.
- The division between two integers always truncates toward zero.
- There will not be any division by zero.
- The input represents a valid arithmetic expression in a reverse polish notation.
- The answer and all the intermediate calculations can be represented in a 32-bit integer.

Example 1:

Input: tokens = ["2","1","+","3","*"] <br>
Output: 9  <br>
Explanation: ((2 + 1) * 3) = 9

```bash
class Solution(object):
    def evalRPN(self, tokens):
        """
        :type tokens: List[str]
        :rtype: int
        """
        st = []

        for c in tokens:
            if c == "+":
                st.append(st.pop() + st.pop())
            elif c == "-":
                second, first = st.pop(), st.pop()
                st.append(first - second)
            elif c == "*":
                st.append(st.pop() * st.pop())
            elif c == "/":
                second, first = st.pop(), st.pop()
                st.append(int(float(first) / float(second)))
            else:
                st.append(int(c))
        
        return st[0]
            
```

說明 : 

這種數字計算的後序 (Postfix) 就是標準的使用 Stack 來計算，包含前序中序也是。

只要遇到運算元 (Operands) 就丟到 stack 中， 遇到運算子 (Operator) 就從裡面拿兩個 Operands 出來計算後，丟回去 stack ，直到結束。 如果結束後 Stack 不是剩下一個值 代表這個 Postfix 有誤。

```
#    
#     
#    | |        | |        | |  (+)   | |         | |   (*)   | |
#    | |  -->   | |   -->  |1|  -->   | |   -->   |3|   -->   | |    Done
#    | |        |2|        |2|        |3|         |3|         |9|    
#    |_|        |_|        |_|        |_|         |_|         |_|
 
#       push(2)      push(1)    pop(1)     push(3)      pop(3)    
#                               pop(2)                  pop(3)
#                               1+2=3                   3*3=9
#                               push(3)                 push(9)
```

### Prefix 

同場加映 : 前序
```bash
# (((5*6) +3) /3) - ((8-2)/3)
tokens = [ "-", "/", "+", "*",  "5"  , "6"  , "3" ,"3"  , "/", "-" ,"8" ,"2" ,"3"]

st = []

for c in tokens[::-1]:
    if c == "+":
        st.append(st.pop() + st.pop())
    elif c == "-":
        st.append(st.pop() - st.pop())
    elif c == "*":
        st.append(st.pop() * st.pop())
    elif c == "/":
        st.append(int(float(st.pop()) / float(st.pop())))
    else:
        st.append(int(c))
```
### Infix 
同場加映 : 中序

中序因為要考慮到 `運算元的順序` ，因此會比較複雜一點。

```bash

token = ["5", "*", "6", "+", "3", "/", "3", "-", "8", "-", "3", "/", "3"]
token = ["9", "-", "6", "/", "2", "*", "3", "+", "10", "-", "9", "+", "3", "*","2"]

def compute(a,b,operator):
    a = float(a)
    b = float(b)
    if operator == '+': return a + b
    if operator == '-': return a - b
    if operator == '*': return a * b
    if operator == '/': return a / b
precedence = {
    '+' : 1,
    '-' : 1,
    '*' : 2,
    '/' : 2
}
operator = ['+', '-', '*', '/']
operator_st = []
operand_st = []
i = 0
while i < len(token):

    if token[i] in operator:

        while operator_st and  precedence[token[i]] <= precedence[operator_st[-1]]:
            b = operand_st.pop()
            a = operand_st.pop()
            data = compute(  a, b, operator_st.pop())
            operand_st.append(data)
        operator_st.append(token[i])

    else:
        operand_st.append(token[i])

    i+=1

while operator_st:
    b = operand_st.pop()
    a = operand_st.pop()
    data = compute(  a, b, operator_st.pop())
    operand_st.append(data)
    
print("Result : ", operand_st[-1])    

```
### Prefix_to_Postfix 

前序轉後序

```bash
prefixTokens = ["-", "/", "+", "*", "5", "6", "3", "3", "/", "-", "8", "2", "3"]
stack = []
operators = {'+', '-', '*', '/'}
for token in prefixTokens[::-1]:
    if token in operators:
        # pop 2 個元素組合 postfix（left right op）
        op1 = stack.pop()
        op2 = stack.pop()
        expr = op1 + op2 + [token]
        stack.append(expr)
    else:
        # 遇到數字，直接放入 stack (作為 list)
        stack.append([token])
        
print(f"Prefix : {prefixTokens}")
print("Doing prefixToPostfix")
print(f"Postfix : {stack[0]}")

```

### Postfix_to_Prefix 

後序轉前序

```bash
postfixTokens = ['5', '6', '*', '3', '+', '3', '/', '8', '2', '-', '3', '/', '-']
stack = []
operators = {'+', '-', '*', '/'}

for token in postfixTokens:
    if token in operators:
        
        first_item = stack.pop()
        second_item = stack.pop()
        
        current_item = [token] + second_item + first_item 
        stack.append(current_item)
    
    else:
        stack.append([token])

print(f"Postfix : {postfixTokens}")
print("Doing postfixToPrefix")
print(f"Prefix : {stack[0]}")
```

---

## 155. Min Stack `(Medium)`

Design a stack that supports push, pop, top, and retrieving the minimum element in constant time.

Implement the MinStack class:

- MinStack() initializes the stack object.
- void push(int val) pushes the element val onto the stack.
- void pop() removes the element on the top of the stack.
- int top() gets the top element of the stack.
- int getMin() retrieves the minimum element in the stack.

You must implement a solution with O(1) time complexity for each function.


Example 1:

Input<br>
["MinStack","push","push","push","getMin","pop","top","getMin"]<br>
[[],[-2],[0],[-3],[],[],[],[]]

Output<br>
[null,null,null,null,-3,null,0,-2]

Explanation <br>
MinStack minStack = new MinStack();<br>
minStack.push(-2);<br>
minStack.push(0);<br>
minStack.push(-3);<br>
minStack.getMin(); // return -3<br>
minStack.pop();<br>
minStack.top();    // return 0<br>
minStack.getMin(); // return -2<br>


```bash
class MinStack(object):

    def __init__(self):
        self.items=[]
        self.min_stack=[]

    def push(self, val):
        self.items.append(val)
        if not self.min_stack or val <=self.min_stack[-1]:
            self.min_stack.append(val)
       
    def pop(self):
        if self.items:
            top_value = self.items.pop()
            if top_value == self.min_stack[-1]:
                self.min_stack.pop()  

    def top(self):
        if self.items:
            return self.items[-1]
        return None
            
    def getMin(self):
        if self.min_stack:
            return self.min_stack[-1]
        return None
```

說明 : 

這一題原本很簡單，但因為題目加了一個限制 `"O(1) time complexity for each function"`，這會導致原本只要維護一個 stack ，變成要維護兩個 stack。

1. 如果不考慮 O(1)，只要用一個 stack 去儲存每次的值
    - stack.append()  --> 尾端加入元素 O(1)
    - stack.pop()   --> 尾端刪除並回傳元素 O(1)
    - stack[-1]    --> 尾端刪除並回傳元素 O(1)
    - min(stack)   --> 遍歷整個stack O(n)
    
2. 用一個變數去儲存 min，每次 push 時判斷是否為最小值並且更新 min。但這樣會引發一個問題，如果今天 pop() 的剛好是最小值，會導致 min 異常。

3. 因此，我們將變數儲存 min，改由 min_stack 儲存 min，每次遇到最小值才會加入到 min_stack 。如果今天最小值被 pop()後，只會遇到兩個情況

    1. min_stack 不為空，下一個是倒數第二小的值
    2. min_stack 為空， stack 也一定為空，整個 stack 沒有任何資料，回傳 None <br>

    Q : 為甚麼 min_stack 為空 stack 就一定為空? 因為在 push() 時第一個判斷的就是 `if not self.min_stack` ，第一個值進來時，不管它是多少，都會被塞入 min_stack，因為它是目前唯一的值，是最大值也是最小值。如果連 stack 中的第一個值也被 pop()，stack 自然為空。


---

# Monotonic Stack

## 496. Next Greater Element I `(Eazy)`

The next greater element of some element x in an array is the first greater element that is to the right of x in the same array.

You are given two distinct 0-indexed integer arrays nums1 and nums2, where nums1 is a subset of nums2.

For each 0 <= i < nums1.length, find the index j such that nums1[i] == nums2[j] and determine the next greater element of nums2[j] in nums2. If there is no next greater element, then the answer for this query is -1.

Return an array ans of length nums1.length such that ans[i] is the next greater element as described above.


### Solution 1
stack儲存的是nums2中的值，並用這些值去比較，因為使用的是值不是index, 所以搭配Dictory，直接對應

```
#    init loop1      loop2     loop3       loop4       loop5
#     
#    | |        | |        | |        | |         | |         | |
#    | |  -->   | |   -->  |1|  -->   |2|   -->   | |   -->   | |    Done
#    | |        |3|        |3|        |3|         |4|         |6|    
#    |_|        |_|        |_|        |_|         |_|         |_|
 
#       push(3)      push(1)    pop(1)     pop(2)      pop(4)    
#                               push(2)    pop(3)      push(6)
#                                          push(4)
```
```bash
# Coding
class Solution(object):
    def nextGreaterElement(self, nums1, nums2):
        """
        :type nums1: List[int]
        :type nums2: List[int]
        :rtype: List[int]
        """
        stack=[]
        mapping={}
        for n in nums2:
            
            while stack and n> stack[-1]:
                
                mapping[stack.pop()]=n
                
            stack.append(n)
        return [mapping.get(n,-1) for n in nums1]
```

### Solution 2
stack儲存的是 Index ,這時候就不需要用dictinory, 而是用list, 這個list就是根據Index  來儲存答案

```bash
class Solution(object):
    def nextGreaterElement(self, nums1, nums2):
        """
        :type nums1: List[int]
        :type nums2: List[int]
        :rtype: List[int]
        """
        stack=[]
        result=[-1] * len(nums2)
        for i in range(len(nums2)):
            while stack and  nums2[i] > nums2[stack[-1]]:
                
                result[stack.pop()] = nums2[i]
            
            stack.append(i)

        return [result[nums2.index(n)]  for n in nums1]
```

## 503. Next Greater Element II (Medium)

Given a circular integer array nums (i.e., the next element of nums[nums.length - 1] is nums[0]), return the next greater number for every element in nums.

The next greater number of a number x is the first greater number to its traversing-order next in the array, which means you could search circularly to find its next greater number. If it doesn't exist, return -1 for this number.

Input: nums = [1,2,1] <br>
Output: [2,-1,2] <br>
Explanation: The first 1's next greater number is 2;  <br>
The number 2 can't find next greater number. 
The second 1's next greater number needs to search circularly, which is also 2.

### Solution 1

Base on Next Greater Element I - Solution 2

```bash
class Solution(object):
    def nextGreaterElements(self, nums):
        """
        :type nums: List[int]
        :rtype: List[int]
        """
        stack = []
        result = [float("inf")] * len(nums)
        for i in range(len(nums)):
            
            while stack and nums[i] >  nums[stack[-1]]:
                result[stack.pop()]=nums[i]
            stack.append(i)

        #print(result)

        for i in range(len(nums)):
            
            if result[i]==float("inf"):
                
                for j in range(len(nums)):
                    if nums[j]>nums[i]:      
                        result[i] = nums[j]
                        break
        #print(result)
        for i in range(len(nums)):
            if result[i]==float("inf"):
                result[i]=-1


        return result
```
### Solution 2

 1. 從最後一個元素往前面去 維護一個Decreasing Monotonic stack，

 2. 如果一直pop直到最後 stack為空的話，代表目前你是最大的

 3. 如果stack不為空的話，代表當前 nums 比 stack[-1]還小  (因為前面有判斷 while stack[-1]<=num)。因此 nums 所在的res 位置就要被設為stack[-1] , 並且將nums加入倒monotomic當作第二大的

 4. 一直到兩輪結束，最大的值不會被更改，搭配預設所有人都是-1
```bash
class Solution(object):
    def nextGreaterElements(self, nums):
        """
        :type nums: List[int]
        :rtype: List[int]
        """

        n = len(nums)
        res = [-1] * n  # Initialize the result array with -1
        stack = [] 
        for i in range(2 * n - 1, -1, -1):
            num = nums[i % n]  # Current element (handle circular index)
            
            # Remove elements from the stack that are <= the current element
            while stack and stack[-1] <= num:
                stack.pop()
            
            # If the stack is not empty, the top of the stack is the next greater element
            if stack:
                res[i % n] = stack[-1]
            
            # Push the current element onto the stack
            stack.append(num)
            
            i-=1

        return res
```
### Solution 3

把nums 變成兩倍 ex: [1,2,3,4,3] + [1,2,3,4,3] 。
這樣就有一個cycle 並且可以直接用 Next Greater Element I 的方法

```bash
class Solution(object):
    def nextGreaterElements(self, nums):
        """
        :type nums: List[int]
        :rtype: List[int]
        """
        stack =[]
        nums_map = {}
        ln = len(nums)
        result = [-1] * (ln*2)
        nums += nums
        for i in range(len(nums)):
            while stack and nums[stack[-1]] < nums[i]:
                result[stack.pop()] = nums[i]
            stack.append(i)

        return  result[:ln]
```

