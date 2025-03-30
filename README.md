# discord-bot-template

## 概要

__※現在製作中のプロジェクトです。予期せぬバグ、不具合などが含まれる可能性があります。__

このプロジェクトは、Discord Botの開発を効率化するためのテンプレートです。
非同期処理、依存性注入、クリーンアーキテクチャを採用し、拡張性と保守性を重視した設計になっています。

## 特徴

### 1. __非同期処理の活用__

- `asyncio`を使用して非同期処理を実現。
- 高速かつ効率的な処理を可能にする設計。

### 2. __依存性注入 (DI)__

- `injector`ライブラリを使用して依存性注入を実現。
- テスト容易性とモジュール間の疎結合を実現。

### 3. __Mediatorパターンの採用__

- `mediator.py`でMediatorパターンを実装。
- リクエストとハンドラーの分離により、コードの可読性と拡張性を向上。

### 4. __クリーンアーキテクチャ__

- ユースケース層 (`usecases/`) とリポジトリ層 (`repository.py`) を明確に分離。
- ビジネスロジックとインフラストラクチャの独立性を確保。

### 5. __コグ (Cog) によるコマンド管理__

- `discord.ext.commands`のCogを使用してコマンドをモジュール化。
- Botの機能を簡単に拡張可能。

### 6. __型安全性__

- Pythonの型ヒントを活用し、静的解析ツールによるエラー検出を強化。

### 7. __テスト環境の整備 (WIP)__

- `pytest`と`pytest-asyncio`を使用したテスト環境を構築。

## ディレクトリ構成

```text
.
├── app/                    # アプリケーション本体
│   ├── __main__.py         # エントリーポイント
│   ├── cogs/               # Cogモジュール
│   ├── container.py        # DIコンテナ設定
│   ├── mediator.py         # Mediatorパターンの実装
│   ├── repository.py       # リポジトリ層
│   └── usecases/           # ユースケース層
├── tests/                  # テストコード
├── .vscode/                # VSCode設定
├── pyproject.toml          # プロジェクト設定
└── README.md               # このファイル
```

## 必要な環境

- パッケージ管理 [uv](https://github.com/astral-sh/uv)
- 必要な依存関係は`pyproject.toml`に記載されています。

## セットアップ

1. 仮想環境を作成:

   ```bash
   uv venv -p 3.10 .venv
   source .venv/bin/activate  # Windows(PS)の場合は .venv\Scripts\activate
   ```

2. 依存関係をインストール:

   ```bash
   uv sync
   ```

3. Botを起動:

   ```bash
   uv run app
   ```

## TODO

- Domain層の拡充
- DBのセットアップ (複数ソリューションに対応)
- ORMによるマイグレーション管理
- 認証、認可の仕組みの導入

## ライセンス

このプロジェクトは[MITライセンス](LICENSE)の下で公開されています。
