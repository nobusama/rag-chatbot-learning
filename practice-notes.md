# Lesson 3 実践ノート：Feature 3 実装の振り返り

**実装日**: 2025-11-10
**実装内容**: Course Outline Tool（コースアウトラインツール）の追加

---

## 実装の概要

### 目標
コースのアウトライン（レッスン一覧）を取得できる新しいツールをバックエンドに追加する

### 達成したこと
- ✅ 新しいバックエンドツール `CourseOutlineTool` を実装
- ✅ システムプロンプトを更新してAIにツールの使い方を教える
- ✅ ツールを登録してシステムで利用可能にする
- ✅ ブラウザでテストして正常動作を確認

---

## 1. アーキテクチャの理解

### システム全体のフロー

```
ユーザーの質問
    ↓
FastAPI (app.py)
    ↓
RAG System (rag_system.py)
    ↓
AI Generator (ai_generator.py) ← システムプロンプト
    ↓
Tool Manager (search_tools.py)
    ↓
CourseOutlineTool / CourseSearchTool
    ↓
Vector Store (vector_store.py)
    ↓
ChromaDB (course_catalog)
```

### 重要なポイント
- 各コンポーネントが明確な役割を持つ
- ツールは`Tool`インターフェースを実装
- `ToolManager`が全ツールを管理
- Vector Storeが2つのコレクションを管理（content と catalog）

---

## 2. 実装の詳細

### 変更したファイル

#### ① `backend/search_tools.py` (140-243行目)

**追加したクラス**: `CourseOutlineTool`

**実装したメソッド**:
```python
class CourseOutlineTool(Tool):
    def __init__(self, vector_store: VectorStore)
        # VectorStoreへの参照を保存
        # last_sourcesを初期化（UI用）

    def get_tool_definition(self) -> Dict[str, Any]
        # ツール名: "get_course_outline"
        # 説明: コースの構造とレッスンリストを取得
        # 入力スキーマ: course_name (string)

    def execute(self, course_name: str) -> str
        # 1. _resolve_course_name()であいまい検索
        # 2. course_catalog.get()でメタデータ取得
        # 3. lessons_jsonをパース
        # 4. _format_outline()で整形
        # 5. _build_sources()でUI用情報を保存

    def _format_outline(...)
        # 読みやすい形式でアウトラインを整形

    def _build_sources(...)
        # UIのクリック可能なリンク情報を構築
```

**データフロー**:
```
course_name (部分一致OK "MCP")
    ↓
_resolve_course_name() → "MCP: Build Rich-Context AI Apps with Anthropic"
    ↓
course_catalog.get(ids=[course_title]) → メタデータ取得
    ↓
json.loads(lessons_json) → レッスンリスト
    ↓
_format_outline() → 整形された文字列
    ↓
_build_sources() → UI用のリンク情報 (last_sources)
```

**学んだこと**:
- ツールは抽象クラス`Tool`を継承する必要がある
- `get_tool_definition()`はAIにツールの存在を知らせる
- `execute()`で実際の処理を実装
- `last_sources`でUIにリンク情報を渡す
- エラーハンドリングが重要（コースが見つからない場合など）

---

#### ② `backend/ai_generator.py` (8-26行目)

**変更内容**: システムプロンプトの更新

**追加したセクション**:
```
Available Tools:

1. **Course Content Search** (search_course_content):
   - Use when: 具体的なトピックや概念について質問されたとき
   - Example questions: "How does X work?", "What are the steps for Y?"
   - Returns: コンテンツの抜粋

2. **Course Outline** (get_course_outline):
   - Use when: コースの構造やレッスン一覧について質問されたとき
   - Example questions: "What lessons are in the MCP course?"
   - Returns: 完全なコース構造
```

**学んだこと**:
- システムプロンプトはAIの行動を決定する最重要要素
- "Use when"でツール選択の条件を明確化
- 例を示すことでAIが正しく判断できる
- ツール間の使い分けを明示することが重要

**ツール選択の判断基準**:
- ❌ "How does MCP work?" → Content Search（内容の説明が必要）
- ✅ "What lessons are in MCP?" → Outline Tool（構造の取得）
- ❌ "Explain prompt compression" → Content Search（詳細情報）
- ✅ "Show course structure" → Outline Tool（全体像）

---

#### ③ `backend/rag_system.py` (7行目、26-27行目)

**変更内容**: ツールの登録

**追加したコード**:
```python
# Import追加
from search_tools import ToolManager, CourseSearchTool, CourseOutlineTool

# ツールの初期化と登録
self.outline_tool = CourseOutlineTool(self.vector_store)
self.tool_manager.register_tool(self.outline_tool)
```

**学んだこと**:
- ツールはインスタンス化して登録する必要がある
- VectorStoreへの参照を渡す（データアクセスのため）
- 登録後、自動的にAIから利用可能になる
- 既存のパターンを踏襲（CourseSearchToolと同じ方法）

---

## 3. プランモードの活用

### 使用したワークフロー

**手順**:
1. `Shift + Tab` を2回押してプランモード起動
2. プロンプトを入力（`@ファイル名`で参照）
   ```
   @backend/search_tools.py @backend/ai_generator.py @backend/rag_system.py

   Add a second tool alongside the existing content-related tool...
   ```
3. Claude Codeが実装計画を作成
4. 計画を確認・承認
5. 自動的に実装を実行

**プランモードのメリット**:
- ✅ 実装前に全体像が見える
- ✅ 複数ファイルの変更を整理できる
- ✅ 間違った方向に進む前に修正できる
- ✅ 学習者として「何が起きるか」を理解できる
- ✅ 複雑な変更でも安心して進められる

---

## 4. 重要な学習ポイント

### A. ツール追加の標準パターン

**3ステップ**:

1. **ツールクラスを作成** (`search_tools.py`)
   - `Tool`抽象クラスを継承
   - `get_tool_definition()`を実装（ツールの定義）
   - `execute()`を実装（実際の処理）
   - エラーハンドリングを含める

2. **システムプロンプトを更新** (`ai_generator.py`)
   - ツールの説明を追加
   - 使用タイミングを明記
   - 例を提供

3. **ツールを登録** (`rag_system.py`)
   - インポート
   - インスタンス化（必要な依存関係を渡す）
   - ToolManagerに登録

**このパターンは他のツール追加でも使える！**

---

### B. Vector Storeの構造

**2つのコレクション**:
- `course_content`: コースの実際のコンテンツ（テキストチャンク）
  - 検索対象のメイン情報
  - CourseSearchToolが使用

- `course_catalog`: コースのメタデータ
  - コースタイトル、講師、リンク
  - レッスン情報（JSON文字列として保存）
  - CourseOutlineToolが使用

**使用したメソッド**:
- `_resolve_course_name(course_name)`: あいまい検索でコース名を特定
- `course_catalog.get(ids=[...])`: 特定のコースのメタデータを取得
- `lessons_json`: JSON文字列として保存されたレッスン情報

---

### C. UIとの連携

**`last_sources`の構造**:
```python
source_dict = {
    "text": "MCP: Build Rich-Context AI Apps with Anthropic - Lesson 1",
    "course_link": "https://...",
    "lesson_link": "https://...",
    "lesson_number": 1
}
```

**UIでの表示**:
- フロントエンドが自動的にクリック可能なリンクとして表示
- Feature 1で実装済みのUI機能と統合
- 追加のフロントエンド変更は不要
- 各レッスンが青いボックスでリンク表示される

---

## 5. テストと確認

### テストした質問

**成功したテスト**:
```
質問: "What is the outline of the 'MCP: Build Rich-Context AI Apps with Anthropic' course?"

結果:
✅ 正しいツール（get_course_outline）が選択された
✅ 全11レッスンが表示された（Lesson 0 - Lesson 10）
✅ 各レッスンに番号とタイトルが含まれる
✅ コースの説明も含まれる
```

### サーバーログの確認

```bash
INFO: 127.0.0.1:57819 - "POST /api/query HTTP/1.1" 200 OK
```
- `200 OK`: リクエスト成功
- エラーなし
- ツールが正常に動作

### デバッグ方法

1. **サーバーログを確認**
   - `BashOutput`ツールで出力を確認
   - エラーがあればスタックトレースを確認

2. **ブラウザで動作確認**
   - 実際に質問を入力
   - レスポンスの内容を確認
   - リンクがクリック可能か確認

3. **APIを直接テスト**
   - `curl http://localhost:8000/api/courses`
   - データが正しくロードされているか確認

---

## 6. 身についたスキル

### 技術的スキル
- ✅ Python抽象クラスの実装
- ✅ Anthropic Tool Calling APIの理解
- ✅ JSONデータの解析
- ✅ Vector Database（ChromaDB）の活用
- ✅ FastAPI/RAGシステムのアーキテクチャ理解
- ✅ システムプロンプトエンジニアリング

### Claude Code操作スキル
- ✅ プランモードの効果的な活用
- ✅ ファイル参照（`@`記法）の使用
- ✅ 複数ファイルの同時編集管理
- ✅ サーバーの起動とモニタリング
- ✅ スクリーンショットでの動作確認

### 開発プロセススキル
- ✅ 計画 → 実装 → テスト のフロー
- ✅ 既存パターンの理解と踏襲
- ✅ エラーハンドリングの考慮
- ✅ 段階的な確認と検証
- ✅ ドキュメント（振り返りノート）の作成

---

## 7. つまずいたポイントと解決方法

### 問題1: /clearで会話履歴が消えた
**状況**: Feature 3を実装しようとしていたところで`/clear`してしまい、コンテキストが失われた

**解決方法**:
- gitステータスで実装済みの内容を確認
- 講義スクリプトで必要な内容を再確認
- プランモードで新しく実装を開始

**学び**: `/clear`は慎重に使う。必要なら`/compact`でサマリーを保持

---

### 問題2: どこから再開すればいいかわからない
**状況**: Feature 1-2は実装済みだが、Feature 3がどこまで進んでいたか不明

**解決方法**:
- `git diff`で変更内容を確認
- 講義スクリプトと照らし合わせ
- 実装状況を整理

**学び**: 定期的にコミットして進捗を記録することが重要

---

## 8. Lesson 3全体の進捗

### ✅ Feature 1: ソース引用のリンク化
**実装内容**:
- バックエンド: `search_tools.py`でリンク情報を含むソースを返す
- フロントエンド: クリック可能なリンクボックスとして表示
- スタイル: ホバー効果付きの青いボックス

### ✅ Feature 2: '+ New Chat'ボタン
**実装内容**:
- HTML: サイドバーに新規チャットボタンを追加
- JavaScript: `handleNewChat()`関数で会話クリア
- CSS: 既存リンクと統一されたスタイル
- 機能: ページリフレッシュなしで新しいセッション開始

### ✅ Feature 3: コースアウトラインツール（本実装）
**実装内容**:
- バックエンド: `CourseOutlineTool`クラスを追加
- システムプロンプト: ツールの使い分けを明記
- ツール登録: RAGシステムに統合
- 動作確認: ブラウザでテスト成功

---

## 9. 次のステップ

### 今後の学習
- **Lesson 4**: テスト、デバッグ、リファクタリング
  - テストの書き方
  - エラーデバッグの方法
  - Sequential tool callingの実装

### 実装の改善案
1. **エラーメッセージの改善**: より具体的なエラー情報
2. **レッスンリンクの検証**: リンクが有効か確認
3. **キャッシング**: 同じコースの繰り返し検索を最適化
4. **追加のツール**: 講師情報取得、コース比較など

### 振り返りの活用
- このノートを定期的に見返す
- 他のツール実装時に参照
- パターンを他のプロジェクトにも適用

---

## 10. 参考資料

### プロジェクト内
- `lesson3-building-features/notes.md`: 理論的な学習内容
- `sc-claude-code-files/reading_notes/L3_notes.md`: 講義スクリプト
- `backend/search_tools.py`: 実装コード
- `backend/ai_generator.py`: システムプロンプト

### 外部ドキュメント
- Claude Code Documentation: https://docs.claude.com/en/docs/claude-code
- Anthropic Tool Use API: https://docs.anthropic.com/en/docs/build-with-claude/tool-use

---

## まとめ

### 実装の成果
新しいバックエンドツール `CourseOutlineTool` を追加し、ユーザーがコースのレッスン一覧を簡単に取得できるようになった。

### 最も重要な学び
**ツール追加の3ステップパターン**:
1. ツールクラス作成
2. システムプロンプト更新
3. ツール登録

このパターンは他のRAGシステムやAI統合プロジェクトでも応用可能。

### 達成感
- ✅ 複雑なバックエンド実装を完遂
- ✅ AIが正しくツールを選択
- ✅ Lesson 3の全Feature完了
- ✅ 実践的なスキルを獲得

**次回**: 実装をコミットして、Lesson 4へ進む準備をする

---

**作成日**: 2025-11-10
**最終更新**: 2025-11-10
