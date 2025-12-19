這一篇文章主要介紹Docker, 並將前面專案所用到的所有技術都轉成Docker。 (Backend, Nginx, Redis, PostgreSQL)


# 主要流程

1. Docker 介紹
2. Docker 使用
3. Docker Compose


#  Docker 介紹

Docker 是一個開源的容器化平台，能夠將 `應用程式與其執行環境` 打包成 <u> 輕量且可攜帶</u> 的容器（Container）。這些容器在任何有安裝 Docker 的系統上，都能一致且快速地運行，避免「環境不一致」的問題。

Docker 利用的是 Linux 核心的 Namespace 和 cgroups 技術。

- Namespace : Linux 隔離機制。將系統資源"虛擬化"，分配給每個容器。總共有六種類型
- Control Groups (cgroups) : 控制每一個隔離容器可使用的資源，避免單個Container使用完所有系統資源。

## Docker 核心組件

- 映像檔 (Image) : "應用程式"運行所需的所有內容，並以此建立容器 (Container)。
- 容器 (Container) : `基於映像檔`產生的輕量級且資源隔離的`運行環境`。
- Docker Engine : 兩部分組成 : 
    - Docker Daemon (守護進程) : 負責`容器生命週期管理`，包含建立、啟動、停止和刪除。
    - Docker Client (客戶端) : `用戶與Docker互動`的命令行工具，發送指令給Daemon。
- 倉庫 (Registry) : 存放和管理Image的集中倉庫。常用的是`公開`的 Docker Hub，也可自行搭建`私有倉庫`。


使用流程說明 (安裝完 Docker):

1. 使用者輸入指令，例如 `docker run redis` ， Docker client會將其送給Docker Daemon
2. Docker Daemon 先在`本地尋找 redis Image"` ，若未找到，則會去預設 `Docker Hub`搜尋並下載
3. 下載完之後，Docker Daemon `根據 "redis Image" 創建一個Container 實例`。
4. Container啟動成功後，裡面就會運行 Redis服務。

---

## - 為什麼要使用 Docker？

- **環境一致性**  
  將應用及所有依賴包裝在容器中，不論開發、測試或生產環境，都能保證相同的運行條件，`減少「我機可運行，他機無法運行」`的狀況。

- **快速部署與啟動**  
  容器啟動速度快，不需要啟動完整作業系統，`節省開發和部署時間`。

- **彈性與擴展性**  
  容器`易於複製和擴展`，方便建構微服務架構及自動化部署流水線 (CI/CD)。

---

## - Docker 與 VM 

在Docker 尚未推出時，是透過建立 VM (Virtual Machine) 來解決「環境不一致」的問題。

VM 其實就是一台完整功能的電腦，只不過是虛擬的。由一台實體電腦所模擬出來。<br>



為甚麼要由一台實體電腦模擬一台虛擬電腦出來? 是因為`當你只有一台電腦，卻同時需要 Windows 的環境 和 Linux 的環境的，甚至更多不同環境`。

如果沒有VM，你只能:
- 方法1 : 買很多台實體電腦，各自灌不同作業系統
- 方法2 : 當你想要用Linux的時候，把電腦重灌成Windows；當你想用Windows的時候把電腦重灌成Linux。

顯然兩種方法都不太可能，因此VM誕生了。

想在自己的電腦中建立VM，有兩個條件。第一個是確認自己的CPU 是不是有支援虛擬化技術 ，再來就是在自己的電腦上安裝Hypervisor。ex: VirtualBox。這樣你的電腦就具備打造 VM 的 能力了。




| 特性           | Docker 容器                     | 虛擬機（VM）                        |
|--------------|----------------------------|--------------------------------|
| 是否需要硬體虛擬化支援 | 不需要                         | 需要       |
| 隔離方式         | 利用 Linux kernel namespace 和 cgroups | 利用 Hypervisor 模擬完整硬體及 OS     |
| 資源消耗         | 輕量，共用核心                   | 重，需運行完整 OS                   |
| 作業系統彈性   |  必須與宿主機核心相容（通常 Linux）  |可跑不同作業系統（Linux、Windows等）|

---


如何選擇?  

- VM : 完整、獨立且強隔離的系統環境，或運行不同作業系統
- Docker : 快速啟動、輕量、易於擴展及持續交付，特別是微服務架構




# Docker 使用
