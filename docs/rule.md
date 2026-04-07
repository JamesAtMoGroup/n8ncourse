# Platform Rules

## 程式規則
- 所有新頁面使用 brand tokens（#000000 bg, #7cffb2 accent）
- n8ncourse/ 內的現有頁面設計不得更動
- Session 一律使用 localStorage，key: `aischool_user`
- 不使用 Supabase
- 所有 API 呼叫走 crmnotetool.zeabur.app

## 內容規則
- Hero 區塊禁止：meta tag badges、上一堂/下一堂導航、頁尾 callout 導航
- 禁止詞：三週、本週、第N週、昨天、關於講師
- Lecture 頁面命名：lectureN/index.html，顯示：Lecture N
- Hero 區塊只保留：badge、h1 標題、subtitle

## Repo 規則
- 所有 lecture 頁面在 n8ncourse/ 子目錄
- 根目錄 courses.json = 課程系列清單
- n8ncourse/courses.json = lecture 清單
- Deploy: Zeabur only

## Agent 規則
- Platform Director 唯一對外溝通
- QA Agent 全 checklist 通過才 deploy
- 任何 checklist 失敗 → 回對應 agent 修正 → 重新驗
