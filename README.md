# AIproject_E-bao
E-bao is a small software that allows users to inquire about their current symptoms via a LINE bot and seek guidance on which hospital or clinic departments they can make an appointment with.
當然可以，這裡是根據你的需求更新過的 README 文件內容，將安裝套件分為批量安裝和個別安裝兩部分：

---

這是一個基於 Django 和 LINE Bot API 的智能醫療助手系統，旨在幫助用戶根據症狀進行初步的疾病分類並提供醫療機構資訊。系統使用了機器學習模型進行症狀分類，並能提供來自衛生署的公告和附近醫療機構的資訊。

## 功能

- **症狀分類**：根據用戶輸入的症狀，進行初步的疾病分類。
- **附近醫療機構查詢**：提供一個連結，讓用戶能查看附近的醫療機構。
- **衛生署公告**：顯示衛生署的最新公告。
- **自定義處理**：處理不同類型的症狀輸入並給出相應建議。

## 安裝步驟

### 批量安裝

1. **克隆倉庫**

   ```bash
   git clone https://github.com/AIProjectTeam2/AIproject_E-bao.git
   cd AIproject_E-bao
   ```

2. **創建虛擬環境並安裝所有依賴**

   ```bash
   python -m venv venv
   source venv/bin/activate  # 在 Windows 上使用 venv\Scripts\activate
   pip install -r requirements.txt
   ```

### 個別安裝

如果你希望個別安裝必要的套件，你可以按照以下步驟進行：

1. **創建虛擬環境**

   ```bash
   python -m venv venv
   source venv/bin/activate  # 在 Windows 上使用 venv\Scripts\activate
   ```

2. **個別安裝所需的套件**

   ```bash
   pip install django
   pip install line-bot-sdk
   pip install numpy
   pip install pandas
   pip install jieba
   pip install joblib
   pip install feedparser
   pip install gensim
   ```

   你可以根據 `requirements.txt` 文件中的套件進行個別安裝。

3. **安裝其他依賴**

   確保安裝 Django 和其他相關套件，這些套件在 `requirements.txt` 中已經列出。

4. **配置 Django**

   - 在 `settings.py` 中配置 LINE Bot API 的憑證 (`LINE_CHANNEL_ACCESS_TOKEN` 和 `LINE_CHANNEL_SECRET`)。
   - 配置資料庫和其他必要的設置。

5. **遷移數據庫**

   ```bash
   python manage.py migrate
   ```

6. **創建和加載機器學習模型**

   確保以下文件存在並位於適當的位置：
   - `word2vec.zh.300.model/word2vec.zh.300.model`
   - `svm_model.pkl`
   - `sub0_svm_model.pkl`
   - `sub1_svm_model.pkl`

   **注意**：如果沒有這些模型文件，你需要訓練並保存這些模型。

## 啟動程式

1. **啟動 Django 開發伺服器**

   在虛擬環境中運行以下命令來啟動 Django 開發伺服器：

   ```bash
   python manage.py runserver
   ```

   這樣可以在 `http://127.0.0.1:8000/` 上訪問你的應用程式。

2. **設置 LINE Bot**

   - 登錄到 [LINE Developers Console](https://developers.line.biz/console)。
   - 配置你的 LINE Bot，並將 webhook URL 設定為你的 Django 伺服器的 `/callback/` 路徑。例如，`http://yourdomain.com/callback/`。
   - 確保你的 LINE Bot 已經啟用並正確連接。

## 使用方法

1. **與 LINE Bot 互動**

   - **輸入 `@附近醫療機構`**：獲取附近醫療機構的資訊。
   - **輸入 `@衛生署公告`**：獲取衛生署的最新公告。
   - **輸入 `@請輸入症狀`**：開始症狀分類流程。
   - **輸入症狀**：根據你的症狀進行分類並提供建議。

## 相關文件

- **`dict.txt`**: 繁體中文字典。
- **`userdict-corpus-v2.txt`**: 自定義字典。
- **`stopwords-zh-v2.txt`**: 繁體中文停用詞列表。

---

