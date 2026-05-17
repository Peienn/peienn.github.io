
# 0. Create Enviroment
 
```bash
docker --version
kubectl version --client
kind version
terraform version

# Kind 建一個本地 k8s cluster (only 1 node)
kind create cluster --name chatroom
# 多個 Node
kind create cluster --name chatroom --config manifests/kind-config.yaml


# 確認
kubectl cluster-info --context kind-chatroom
kubectl get nodes

```

# 1. 學習 k8s  **auto-healing with Readiness and Liveness** 

## 流程說明：

透過 Liveness Probe 呼叫 Pod API ，檢查 Pod是不是還活著，再透過 Readiness Probe 呼叫 Pod API 檢查是否可以將流量導入 Pod。兩者獨立，Pod可以是健康狀態但不導入流量 (Liveness: OK, Readiness: Failed)


更深入的背後邏輯是：每台 Node 上的kubelet 會去跑 Probe, 並將回傳結果告知 API Server， 當API Server 收到 kubelet 通知後會去更新 Endpoints 資訊，而 kube-proxy 監聽 Endpoint上的資源，最終決定實際流量要走向哪一個IP。


Node: kubelet, kube-proxy
   - kubelet: 負責執行 probe，回報結果給 API Server。
   - kube-proxy: 監聽 Endpoints 變化，更新 iptables 規則，實際控制流量走向。
  
k8s Control Plan: API Server
   - API Server:接收 kubelet 的回報，更新資源狀態
  
k8s Resources: Endpoints
   - Endpoints: 記錄 Service 底下哪些 pod IP 可用



app.js_v1 : 每呼叫10次就會自動crash 
main.tf_v1 : 建立 k8s Deployment
```bash
#1 build image & load into kind
build image -t chatapp:v1 .
kind load docker-image chatapp:v1 --name chatroom

#2 terraform 執行 k8s (在main.tf 目錄下)
terraform apply -auto-approve

# 完成。接下來驗證當POD shutdown 後會不會 auto-healing 

# 由於程式碼寫了呼叫10次就會crash 所以先連通 Pod Port 再呼叫
# 執行前可先開另外一個 CMD , Run : kubectl get pods -w 觀看過程
kubectl port-forward svc/chatapp 8080:80
for i in {1..10}; do curl http://localhost:8080; echo; done

# 此時可以發現一個 Pod Crash, 但過一下就會被 Restart
# 同樣你也可以執行 kubectl delete pod "NAME" 就會發現 POD雖然被刪除了但馬上又會補上一個


# 可以看到 pod 是跑在哪些 node上
kubectl get pods -n dev -o wide 

```

## 使用文件： 
- main.tf_v1
- app.js_v1


# 2. 學習 k8s  **HPA 自動擴增**

## 說明
流量暴增時，可以根據搜集到的 metric, 設定條件，如果達標的話就擴增 Pod．


## 方法

HPA (k8s原生)  + metrics-server (Download)

```bash
# 找一個資料夾存放 components.yaml
curl -L -O https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml`
kubectl apply -f components.yaml

# metrics-server 預設要驗證每個 node 的 TLS 憑證,加上這個參數，告訴 metrics-server不要驗證 TLS 憑證，直接信任。
kubectl patch deployment metrics-server -n kube-system --type='json' -p='[{"op":"add","path":"/spec/template/spec/containers/0/args/-","value":"--kubelet-insecure-tls"}]'
kubectl get pods -n kube-system | grep metrics
# metrics-server 抓到數據
kubectl top nodes
kubectl top pods

# 在main.tf下面加入 resource hpa
# 如果 hpa 有指定 min_replicas ，這個值會蓋掉 Deployment-replicas

# 驗證是否會擴增 Pod，多開幾個CMD
CMD1 : kubectl get pods -w. # 觀察 Pod 建置 
CMD2 : kubectl get hpa -w。 # 觀察 Pod CPU 是否碰觸 target

# 開一個壓測 pod
kubectl run loadtest --image=busybox --restart=Never -- sh -c "while true; do wget -q -O- http://chatapp/; done"

# 接下來應該就會在hpa 看到 CPU Hgiher, pod 開始擴建。


```

## 使用文件： 
- main.tf_v2
- app.js_v2

# 3. Rolling Update (zero-downtime)

## 部署方式

假設有 3 個 v1 Pod ，準備更新成 v2 Pod。Rolling Update的方法是先新增一個 v2 Pod ,確定沒問題後刪除一個 v1 Pod
(此時依舊是 3 個 Pod , 2*v1 + 1*v2) ，接著再新增一個 v2 Pod 確定沒問題後刪除一個 v1 Pod (此時是 1*v1 + 2*v2)，最後新增一個 v2 確定沒問題後刪除最後一個 v1 。這樣就可以做到零停機的部署。

```bash
# 一樣用 kubectl get pods -w 可以觀察 pod 的新增/刪除順序
```

如果版本更新有問題，有兩種方式退版

1. kubectl rollout undo : 直接退版，速度快。但是會導致 k8s 與 terraform 版本不一致，可以從 terraform plan 發現。適合緊急回滾
2. 修改 main.tf + terraform apply : 就是正常去修改 terraform 裡面 container的version後重新apply。正常操作且k8s與 terraform 兩邊版本都一致。 



## 使用文件： 
- main.tf_v3
- app.js_v2


# 4. Namespace (環境隔離)

Namespace 是 k8s 裡的隔離空間，把資源分開管理：

- default         
- kube-system     → k8s 系統元件（metrics-server 等）
- dev             → 開發環境
- staging         → 測試環境
- prod            → 生產環境

## 使用文件： 
- main.tf_v4


# 5. Ingress 路由

根據自定義的規則，來決定這個流量要導入到哪一個服務上。例如可以設定URL是 /app時要將流量導向 Server1 (name=chatapp), URL是v2時 要將流量導入到 Server2 (name=chatapp-v2)


1. 下載 ingress-nginx.yaml（kind 專用版
   - ingress controller 自動跑在 control-plane，對齊 port mapping (80→80)
2. 建立新的 Deployment2 + service2
3. 在 main.tf 中建立 Ingress resource，定義路由規則
   - /app --> chatapp v3
   - /v2 --> chatapp v4
    
4. terraform apply -auto-approve
5. check:
   1. curl http://localhost/app --> v3
   2. curl http://localhost/v2. --> v4
   

## 使用文件： 
- main.tf_v5
- app_v2

# RBAC (Role-Based Access Control)

控制誰能對哪些資源做什麼動作，原則是最小權限，只給它需要的權限，不多給。


- 誰: ServiceAccount / User
- 資源: Pod / Deployment / Secret
- 操作: get / list / create / delete

- Role            → 權限定義（能做什麼）
- RoleBinding     → 把身份跟權限綁在一起

常見的用途:
| ServiceAccount | 給的權限 | 用途 |
|---|---|---|
| monitor | get / list / watch pods | Prometheus 抓 metrics |
| deployer | create / update deployments | CI/CD 部署新版本 |
| logger | get / list pods/logs | 日誌收集系統 |
| readonly | get / list 所有資源 | 開發者查看 prod 環境 |



## 實測：

目標: 建立一個帳號並且綁定 Read Only 的 Role給它，驗證是不是真的只能 Read

準備: 
 1. main.tf_v6 （建立 serviceAccount + role + role_binding）  
 2. 建置 Pod 
```
kubectl apply -f - <<EOF
apiVersion: v1
kind: Pod
metadata:
  name: test-monitor
  namespace: dev
spec:
  serviceAccountName: monitor
  containers:
  - name: kubectl
    image: bitnami/kubectl
    command: ["sleep", "3600"]
EOF
```
3. 進入 Pod 並且輸入指令
```bash
kubectl exec -it test-monitor -n dev -- sh
# Success
kubectl get pods

# Fail
kubectl delete pods "name"

# exit
exit
```
## 使用文件： 
- main.tf_v6


