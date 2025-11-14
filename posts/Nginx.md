Nginx 是甚麼以及如何用?

# 主要流程 
1. Nginx 介紹
2. Nginx 安裝
3. Nginx 使用
4. Nginx + 實際案例(多人聊天室)




## 1. Nginx 介紹

Nginx 是輕量且高效能的 Web 伺服器（Web Server），負責扮演網站的「接待員」角色。<br>
當使用者訪問你的網站時，Web Server 會接收請求，尋找對應的資源（如網頁、圖片、影片等），再將這些資料傳送回使用者端。


![Nginx](diff.png)

從上圖可以看出發現，沒有Nginx的情況下，由使用者決定要去連到哪一台後端伺服器來獲取資訊，<br>但如果今天採用了Nginx，就會變成是使用者連線到Nginx，由Nginx來決定是哪一台後端伺服器提供資訊。至此可知，後端伺服器會有好幾台且都是相同的服務。

### Nginx 主要特色:
1. 反向代理（Reverse Proxy） : Nginx 作為使用者與後端伺服器間的中介，負責將請求轉發到指定的後端伺服器。
2. 負載平衡（Load Balancing）: Nginx 可根據設定的策略（如輪詢、IP hash）將流量分配到多台後端伺服器，提高效能與可靠性。
<br>
<br>
### 衍伸問題:


Q1 : 平常用Flask or React 等等網站開發工具也都有相同功能，這樣有用到Web Server?<br>
A1 : 這些都是**開發用的伺服器**，讓你可以快速啟動和測試而已。真正的Web Server是有「獨立軟體」負責接收並回應 HTTP 請求。ex: GitHub Pages、Nginx、Microsoft IIS。

Q2 : 不用Web Server也可以的話，為甚麼要用?<br>
A2 : 開發環境可以不用，但是生產環境需要用。因為生產環境會遇到各種情況，例如駭客攻擊、大量用戶連線時系統無法負荷等等。Nginx可以透過反向代理去處理安全性問題(隱藏後端伺服器IP或是過濾惡意請求)、透過負載平衡去處理流量問題，提高系統的可用性與穩定性。

Q3 : 為甚麼Web Server可以處理流量問題?<br>
A3 :  沒有Web Server的情況，開發伺服器需要同時處理 "靜態" 和 "動態" 的需求，造成資源競爭與效能瓶頸。
- 靜態: Html, JavaScript, Css, ... etc
- 動態: API, Database, ... etc <br>

加入了Web Server之後
- **靜態資源以及流量分配** 由 Web Server 負責
- **動態資源** 由後端伺服器負責

---

## 2. Nginx 安裝

### -Linux : 直接進入os
```markdown
# 保持套件是最新版本
sudo apt update
# 安裝 Nginx
sudo apt install nginx
# 啟動 Nginx
sudo systemctl start nginx
# 檢查 Nginx 是否正在執行
sudo systemctl status nginx
# 進入首頁
http://localhost/    --> Welcome to nginx
```
### -Windows : 下載Nginx軟體包，並放到你想放置的位置 例如 C:\nginx\
```markdown
# 切換路徑
cd c:\nginx
# 開啟nginx
.\nginx.exe
# 進入首頁
http://localhost/    --> Welcome to nginx
```
---


## 3. Nginx 使用

概念就是把 "靜態資源" 都放在剛剛起的Nginx Server上面，直接由Nginx提供。<br>
而動態資源(如API、後端應用)則由 Nginx 作為反向代理，轉發請求給後端伺服器。設定寫在nginx.conf。

---

Nginx 的設定有多種方式可以實現流量處理，常見兩種方法，各有優缺點：

1. 多台 Server 開啟相同服務
2. **單台 Server 開啟相同服務（不同 Port）**  

因為專案需求為簡單實作，所以採用方法二。

|方法|優點|缺點|適用場景|
|--|--|--|--|
|多台 Server 開啟相同服務| - 可用性高，容錯性佳<br>- 容易水平擴展<br>- 可分散大量流量 | - 部署和管理較複雜<br>- 需跨伺服器資料同步和協調 | 大型生產環境<br>高流量需求 |
|單台 Server 多個 Port 實例  | - 部署快速簡單<br>- 節省硬體成本<br>- 適合開發與測試環境 | - 受限於單機資源<br>- 單點故障風險<br>- 不適合高流量場景 | 小型專案<br>開發測試環境  |
---

## 4. 搭配專案的題目 : 多人聊天室 

原本多人聊天室的架構 : 
- 後端伺服器 * 1
- 服務 * 1 (Port:5000)

![Nginx](ori_practice.png)

加入Nginx後會變成下圖。多一個服務 (Port:5001) 是為了要實現 "流量控制" 的效果。<br>
- <span style="color:green">網頁伺服器 * 1 (Web Server)</span>
- 後端伺服器 * 1
- 服務 * 1 (Port:5000) +  <span style="color:green">服務 * 1 (Port:5001)</span>

![Nginx](Nginx_practice.png)


--- 


steps 1: 啟動多人聊天室的後端伺服器

```markdown
npm run dev
```

steps 2: 啟動Nginx

```markdown
start nginx
```

steps 3: 把前端的東西放到Nginx內 (如前述所說，靜態資源由Web Server提供)

```markdown
npm run build
```
