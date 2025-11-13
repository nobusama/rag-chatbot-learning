# Subagent活用テンプレート

## 基本パターン

### 2つのSubagent（最も一般的）

```
Use 2 parallel subagents to [タスク内容].

Subagent 1: [視点1 - 例: Minimal changes approach]
Subagent 2: [視点2 - 例: Robust & extensible approach]

Compare the approaches and recommend the best one for [プロジェクト名/状況].
Do not implement any code yet.
```

---

## よくある使い分けパターン

### パターン1: シンプル vs 堅牢

```
Subagent 1: Quick and simple implementation
Subagent 2: Comprehensive and robust implementation
```

**使う場面:**
- リファクタリング
- バグ修正
- 新機能の追加

---

### パターン2: 技術スタックの比較

```
Subagent 1: Propose [技術A] solution (例: REST API)
Subagent 2: Propose [技術B] solution (例: GraphQL)
```

**使う場面:**
- アーキテクチャ設計
- ライブラリ選定
- データベース選択

---

### パターン3: 異なる優先順位

```
Subagent 1: Focus on performance
Subagent 2: Focus on maintainability
```

**使う場面:**
- パフォーマンス最適化
- コード品質改善
- トレードオフの判断

---

## 3つのSubagentを使う場合（応用）

```
Use 3 parallel subagents to [タスク内容].

Subagent 1: Focus on [視点1]
Subagent 2: Focus on [視点2]
Subagent 3: Focus on [視点3]
```

**例:**
```
Subagent 1: Focus on performance (速度重視)
Subagent 2: Focus on security (セキュリティ重視)
Subagent 3: Focus on cost (コスト重視)
```

---

## 避けるべきパターン

### ❌ 役割が曖昧
```
Use 2 parallel subagents to think about this.
```
→ 両方が同じような答えを出す可能性

### ❌ Subagentが多すぎる
```
Use 5 parallel subagents...
```
→ 情報過多で混乱

### ❌ 実装を先にしてしまう
```
Use 2 parallel subagents to implement...
```
→ 比較検討なしで実装が進んでしまう

---

## 経験を積むための練習課題

### 初級: 2つのSubagentで比較

自分のプロジェクトで：
1. リファクタリングしたいコードを選ぶ
2. このテンプレートを使って2つのアプローチを提案させる
3. どちらが良いか自分で判断する

### 中級: 異なる視点を試す

同じ問題に対して：
1. performance vs maintainability
2. simple vs robust
3. new feature vs extend existing

などの異なる視点で比較してみる

### 上級: 3つのSubagentで多角的分析

複雑な問題に対して3つの異なる視点から分析

---

## チェックリスト

良いSubagent活用かチェック：

- [ ] 各Subagentの役割が明確か？
- [ ] 2-3個のSubagentに収まっているか？
- [ ] "Do not implement any code yet" を含んでいるか？
- [ ] 比較検討できる構造になっているか？

---

**作成日**: 2025-11-13
**参考**: Lesson 4 Part 2 - Sequential Tool Calling
