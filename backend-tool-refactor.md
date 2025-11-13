# Backend Tool Refactor: Sequential Tool Calling

## 目的

`backend/ai_generator.py`をリファクタリングして、Claudeが最大2回のツール呼び出しを順次実行できるようにする。

---

## プロンプト

```
Refactor @backend/ai_generator.py to support sequential tool calling where Claude can make up to 2 tool calls in separate API rounds.

Current behavior:
- Claude makes 1 tool call → tools are removed from API params → final response
- If Claude wants another tool call after seeing results, it can't (gets empty response)

Desired behavior:
- Each tool call should be a separate API request where Claude can reason about previous results
- Support for complex queries requiring multiple searches for comparisons, multi-part questions, or when information from different courses/lessons is needed

Example flow:
1. User: "Search for a course that discusses the same topic as lesson 4 of course X"
2. Claude: get course outline for course X → gets title of lesson 4
3. Claude: uses the title to search for a course that discusses the same topic → returns course information
4. Claude: provides complete answer

Requirements:
- Maximum 2 sequential rounds per user query
- Terminate when: (a) 2 rounds completed, (b) Claude's response has no tool_use blocks, or (c) tool call fails
- Preserve conversation context between rounds
- Handle tool execution errors gracefully

Notes:
- Update the system prompt in @backend/ai_generator.py
- Update the test @backend/tests/test_ai_generator.py
- Write tests that verify the external behavior (API calls made, tools executed, results returned) rather than internal state details.

Use two parallel subagents to brainstorm possible plans. Do not implement any code.
```

---

## 使い方

### ステップ1: Plan modeをONにする

### ステップ2: このファイルを参照
```
@backend-tool-refactor.md
```

### ステップ3: Claude Codeが計画を作成
- 2つのSubagentsが異なる実装案を提案
- 実装前に計画を確認
- 承認後に実装開始

---

## 期待される結果

1. **2つの実装案が提案される**:
   - Approach 1: 最小変更アプローチ
   - Approach 2: 堅牢で拡張性の高いアプローチ

2. **各案のメリット・デメリット**が明確に示される

3. **最適な案を選択**して実装を進める

---

## 実装完了後の確認事項

- [ ] システムプロンプトが更新されている
- [ ] `_handle_tool_execution()`がループロジックを含む
- [ ] 新しいテストが追加されている（3つ推奨）
- [ ] 全テストがパス（既存 + 新規）
- [ ] 実際のアプリケーションで動作確認

---

**作成日**: 2025-11-13
**用途**: Lesson 4 Part 2 - Sequential Tool Calling
**ステータス**: 完了 ✅
