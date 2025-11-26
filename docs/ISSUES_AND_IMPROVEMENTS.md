# プロジェクト課題・改善点リスト

最終更新日: 2025-11-26

このドキュメントは、プロジェクトの技術的な課題と改善提案をまとめたものです。

---

## 🔴 優先度: 高（早急な対応推奨）

### 1. ORMモデルのタイムスタンプフィールドが文字列型

**対象ファイル**: `app/infrastructure/orm_models/user_orm.py:7-8`

**現状の問題**:

```python
created_at: str | None = Field(default=None)
updated_at: str | None = Field(default=None)
```

- 日時データを文字列として保存しているため、型安全性が損なわれる
- 自動更新機能がないため、手動でタイムスタンプを管理する必要がある
- 日時計算やソートが困難
- データベースレベルでの日時検証ができない

**推奨される修正**:

```python
from datetime import datetime
from sqlalchemy import func

created_at: datetime | None = Field(
    default=None,
    sa_column_kwargs={"server_default": func.now()}
)
updated_at: datetime | None = Field(
    default=None,
    sa_column_kwargs={
        "server_default": func.now(),
        "onupdate": func.now()
    }
)
```

**影響範囲**:

- ORMモデル変更に伴うマイグレーションの作成が必要
- ドメイン集約への変換ロジックの修正が必要
- 既存のテストケースの修正が必要

**推定工数**: 2-3時間

---

### 2. ドメイン層でのメールアドレス検証の欠如

**対象ファイル**: `app/domain/aggregates/user.py:10-12`

**現状の問題**:

```python
def __post_init__(self) -> None:
    if not self.name:
        raise ValueError("User name cannot be empty.")
    # メールアドレスの検証がない！
```

- 不正なメールアドレスでユーザーが作成可能
- ビジネスルールの欠如
- データ整合性の問題

**推奨される修正**:

```python
import re
from typing import ClassVar

@dataclass
class User:
    EMAIL_REGEX: ClassVar[re.Pattern[str]] = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )

    id: int
    name: str
    email: str

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("User name cannot be empty.")
        if not self.email:
            raise ValueError("User email cannot be empty.")
        if not self.EMAIL_REGEX.match(self.email):
            raise ValueError(f"Invalid email format: {self.email}")
```

**影響範囲**:

- ドメイン集約のテストケース追加が必要
- 既存のテストデータが正しいメール形式か確認が必要

**推定工数**: 1-2時間

---

### 3. データベース一意制約違反のエラーハンドリング欠如

**対象ファイル**: `app/infrastructure/repositories/generic_repository.py:89-106`

**現状の問題**:

- 重複メールアドレスでユーザー登録すると `SQLAlchemyError` として扱われる
- ビジネスエラー（既に存在する）とインフラエラー（DB接続失敗等）が区別されない
- ユーザーに適切なエラーメッセージを返せない

**推奨される修正**:

1. `app/repository.py` にエラータイプを追加:

```python
class RepositoryErrorType(Enum):
    NOT_FOUND = auto()
    UNEXPECTED = auto()
    CONFLICT = auto()  # 追加
```

2. `generic_repository.py` のsaveメソッドを修正:

```python
from sqlalchemy.exc import IntegrityError

async def save(self, entity: T) -> Result[T, RepositoryError]:
    try:
        orm_instance = domain_to_orm(entity)

        if orm_instance.id is None:
            self._session.add(orm_instance)
            await self._session.flush()
        else:
            orm_instance = await self._session.merge(orm_instance)
            await self._session.flush()

        return Ok(orm_to_domain(orm_instance))
    except IntegrityError as e:
        logger.warning("Integrity constraint violated: %s", e)
        err = RepositoryError(
            type=RepositoryErrorType.CONFLICT,
            message="Entity with unique constraint already exists"
        )
        return Err(err)
    except SQLAlchemyError as e:
        logger.exception("Database error occurred in save")
        err = RepositoryError(
            type=RepositoryErrorType.UNEXPECTED,
            message=str(e)
        )
        return Err(err)
```

3. ユースケースでのエラーマッピング:

```python
# app/usecases/users/create_user.py
case Err(repo_error):
    if repo_error.type == RepositoryErrorType.CONFLICT:
        uc_error = UseCaseError(
            type=ErrorType.VALIDATION_ERROR,
            message="User with this email already exists"
        )
    else:
        uc_error = UseCaseError(
            type=ErrorType.UNEXPECTED,
            message=repo_error.message
        )
    return Err(uc_error)
```

**影響範囲**:

- リポジトリ層のエラーハンドリング修正
- ユースケース層のエラーマッピング修正
- 新しいテストケースの追加（重複登録のテスト）

**推定工数**: 2-3時間

---

## 🟡 優先度: 中（計画的な対応推奨）

### 4. グローバル変数によるデータベース状態管理

**対象ファイル**: `app/infrastructure/database.py:9-10`

**現状の問題**:

```python
_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None
```

- グローバル変数による状態管理
- テスト時の状態リセットが複雑になる可能性
- マルチテナント環境では不適切
- 複数データベース接続の管理が困難

**現状の評価**:

- 単一Botインスタンスの運用では実用上問題なし
- テストでは `conftest.py` で適切に管理されている

**将来的な改善案**:

1. DIコンテナでエンジンを管理する設計に変更
2. データベース接続をサービスクラスとして抽象化

**例**:

```python
# app/infrastructure/database_service.py
class DatabaseService:
    def __init__(self, database_url: str) -> None:
        self._engine = create_async_engine(database_url)
        self._session_factory = async_sessionmaker(self._engine)

    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        return self._session_factory

# app/container.py
class AppModule(Module):
    def configure(self, binder: Binder) -> None:
        db_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./bot.db")
        db_service = DatabaseService(db_url)
        binder.bind(DatabaseService, to=db_service, scope=singleton)
        binder.bind(
            IUnitOfWork,
            to=lambda: SQLAlchemyUnitOfWork(db_service.session_factory),
            scope=request
        )
```

**推定工数**: 3-4時間

---

### 5. ハードコードされた Domain-ORM マッピング辞書

**対象ファイル**: `app/infrastructure/repositories/generic_repository.py:21-23`

**現状の問題**:

```python
DOMAIN_TO_ORM_MAP: dict[type, type[SQLModel]] = {
    User: UserORM,
}
```

- 新しいエンティティを追加するたびに手動更新が必要
- スケールしにくい設計
- マッピング忘れのリスク

**改善案1: デコレータによる自動登録**

```python
# app/infrastructure/orm_models/mapper.py
from typing import Any

_DOMAIN_TO_ORM_MAP: dict[type, type[SQLModel]] = {}

def orm_for(domain_type: type) -> Any:
    """Decorator to register ORM-Domain mapping."""
    def decorator(orm_class: type[SQLModel]) -> type[SQLModel]:
        _DOMAIN_TO_ORM_MAP[domain_type] = orm_class
        return orm_class
    return decorator

def get_orm_type(domain_type: type) -> type[SQLModel]:
    """Get ORM type for domain type."""
    orm_type = _DOMAIN_TO_ORM_MAP.get(domain_type)
    if orm_type is None:
        raise ValueError(f"No ORM mapping found for {domain_type}")
    return orm_type

# 使用例
# app/infrastructure/orm_models/user_orm.py
from app.domain.aggregates.user import User

@orm_for(User)
class UserORM(SQLModel, table=True):
    __tablename__ = "users"
    # ...
```

**改善案2: ドメインクラスに属性を持たせる**

```python
# app/domain/aggregates/user.py
@dataclass
class User:
    __orm_type__ = None  # Will be set by infrastructure layer

    id: int
    name: str
    email: str

# app/infrastructure/orm_models/user_orm.py
# モジュールロード時に設定
User.__orm_type__ = UserORM
```

**推定工数**: 4-5時間

---

### 6. Mediator のメタクラスによる自動登録の脆弱性

**対象ファイル**: `app/mediator.py:28-53`

**現状の問題**:

```python
class MediatorMeta(type):
    def __new__(
        mcs,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
    ) -> type:
        cls = super().__new__(mcs, name, bases, namespace)

        # __orig_bases__ を使用した型推論
        if hasattr(cls, "__orig_bases__"):
            for base in cls.__orig_bases__:  # type: ignore[attr-defined]
                # ...
```

- `__orig_bases__` へのアクセスはPythonの内部実装に依存
- Pythonバージョンアップ時に動作しなくなるリスク
- デバッグが困難

**現状の評価**:

- Python 3.12で正常動作している
- 実用上の問題は発生していない

**将来的な改善案**:
明示的な登録メカニズムへの移行

```python
# app/mediator.py
class Mediator:
    _handlers: dict[type, Any] = {}

    @classmethod
    def register[TRequest, TResponse](
        cls,
        request_type: type[TRequest],
        handler: RequestHandler[TRequest, TResponse]
    ) -> None:
        """Explicitly register a handler for a request type."""
        cls._handlers[request_type] = handler

    @classmethod
    async def send_async[TResponse](
        cls, request: Request[TResponse]
    ) -> TResponse:
        request_type = type(request)
        if request_type not in cls._handlers:
            raise ValueError(f"No handler for {request_type}")
        handler = cls._handlers[request_type]
        return await handler.handle(request)

# 使用例
# app/__main__.py または app/container.py で登録
Mediator.register(GetUserQuery, container.get(GetUserHandler))
Mediator.register(CreateUserCommand, container.get(CreateUserHandler))
```

**推定工数**: 6-8時間（全ハンドラーの登録処理を含む）

---

### 7. テストの並列実行への対応不足

**対象ファイル**: `tests/conftest.py`

**現状の問題**:

- テストが順次実行を前提としている
- データベース状態のクリーンアップが暗黙的
- `pytest-xdist` による並列実行時に競合する可能性

**推奨される改善**:

```python
# tests/conftest.py
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.fixture
async def clean_database(session: AsyncSession) -> None:
    """Clean database before each test."""
    # テスト前にロールバック
    await session.rollback()
    yield
    # テスト後にロールバック
    await session.rollback()

@pytest.mark.anyio
async def test_example(
    uow: IUnitOfWork,
    clean_database: None  # フィクスチャを明示的に使用
) -> None:
    # テスト本体
    pass
```

**並列実行の有効化**:

```bash
# pyproject.toml に追加
[dependency-groups]
dev = [
    # ...
    "pytest-xdist>=3.5.0",
]

# 並列実行
uv run --frozen pytest -n auto
```

**推定工数**: 2-3時間

---

### 8. Discord コマンドの入力検証・セキュリティ対策不足

**対象ファイル**: `app/cogs/users_cog.py`

**現状の問題**:

- レート制限なし → スパム攻撃に脆弱
- 権限チェックなし → 誰でもコマンド実行可能
- コマンド引数の詳細なバリデーションなし

**推奨される改善**:

1. **レート制限の追加**:

```python
from discord.ext import commands

@commands.cooldown(rate=5, per=60.0, type=commands.BucketType.user)
@users.command(name="create")
async def users_create(
    self,
    ctx: commands.Context[commands.Bot],
    name: str,
    email: str
) -> None:
    # ...
```

2. **権限チェック**:

```python
from discord import app_commands

@commands.has_permissions(administrator=True)
@users.command(name="create")
async def users_create(self, ctx, name: str, email: str) -> None:
    # ...

# または、カスタムチェック
def is_moderator():
    async def predicate(ctx: commands.Context) -> bool:
        moderator_role = ctx.guild.get_role(MODERATOR_ROLE_ID)
        return moderator_role in ctx.author.roles
    return commands.check(predicate)

@is_moderator()
@users.command(name="delete")
async def users_delete(self, ctx, user_id: int) -> None:
    # ...
```

3. **入力検証の強化**:

```python
@users.command(name="create")
async def users_create(
    self,
    ctx: commands.Context[commands.Bot],
    name: str,
    email: str
) -> None:
    # 入力長制限
    if len(name) > 255 or len(email) > 255:
        await ctx.send("❌ Name or email is too long (max 255 characters)")
        return

    # 特殊文字チェック
    if not name.isprintable():
        await ctx.send("❌ Name contains invalid characters")
        return

    # ユースケース実行
    # ...
```

**推定工数**: 3-4時間

---

## 🟢 優先度: 低（任意・将来的な改善）

### 9. テストカバレッジの向上

**現状**: 77.32%

**カバレッジが低いモジュール**:

- `app.core.result.py`: 63.64% → `combine()` 関数のテスト不足
- `app.infrastructure.database.py`: 59.09% → 初期化処理のテスト不足
- `app.__main__.py`: 0% → 統合テスト・E2Eテスト未実装

**推奨される追加テスト**:

1. **Result型のcombine関数**:

```python
# tests/core/test_result.py
@pytest.mark.anyio
async def test_combine_all_ok() -> None:
    results = [Ok(1), Ok(2), Ok(3)]
    combined = combine(results)
    assert isinstance(combined, Ok)
    assert combined.value == (1, 2, 3)

@pytest.mark.anyio
async def test_combine_with_error() -> None:
    results = [Ok(1), Err("error"), Ok(3)]
    combined = combine(results)
    assert isinstance(combined, Err)
    assert combined.error == "error"
```

2. **データベース初期化**:

```python
# tests/infrastructure/test_database.py
@pytest.mark.anyio
async def test_init_db() -> None:
    from app.infrastructure.database import init_db, _engine

    await init_db("sqlite+aiosqlite:///:memory:")
    assert _engine is not None
```

3. **E2Eテスト（Discord Bot統合テスト）**:

```python
# tests/e2e/test_bot_commands.py
import pytest
from discord.ext import commands
from unittest.mock import AsyncMock

@pytest.mark.anyio
async def test_users_get_command() -> None:
    bot = commands.Bot(command_prefix="!")
    cog = UsersCog(bot)

    # Mockコンテキスト作成
    ctx = AsyncMock()
    ctx.send = AsyncMock()

    # コマンド実行
    await cog.users_get(ctx, user_id=1)

    # 検証
    ctx.send.assert_called_once()
```

**推定工数**: 4-6時間

---

### 10. 未追跡ファイルのGit管理

**現状**:

```
?? app/core/
?? app/usecases/result.py
?? app/usecases/users/
?? tests/test_container.py
?? tests/usecases/users/
```

**推奨アクション**:

```bash
git add app/core/
git add app/usecases/result.py
git add app/usecases/users/
git add tests/test_container.py
git add tests/usecases/users/
git commit -m "Add untracked files to version control"
```

**影響範囲**: なし（単純なGit操作）

**推定工数**: 5分

---

### 11. ログ設定の一元管理

**現状の問題**:

- 各モジュールで `logger = logging.getLogger(__name__)` を個別に定義
- ログレベルやフォーマットの一元管理がない
- 本番環境とテスト環境でログ設定を切り替えにくい

**推奨される改善**:

```python
# app/logging_config.py
import logging
import sys
from typing import Literal

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

def setup_logging(
    level: LogLevel = "INFO",
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
) -> None:
    """Configure application-wide logging."""
    logging.basicConfig(
        level=getattr(logging, level),
        format=format,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("bot.log", encoding="utf-8")
        ]
    )

    # サードパーティライブラリのログレベル調整
    logging.getLogger("discord").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

# app/__main__.py
from app.logging_config import setup_logging

async def main() -> None:
    log_level = os.getenv("LOG_LEVEL", "INFO")
    setup_logging(level=log_level)  # type: ignore[arg-type]
    # ...
```

**.env.example への追加**:

```bash
# ログレベル (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL=INFO
```

**推定工数**: 1-2時間

---

### 12. 設定管理の改善

**現状の問題**:

- 環境変数が `__main__.py` や `database.py` で直接読み込まれている
- デフォルト値が各所に散在
- 設定の一覧性が低い

**推奨される改善**:

```python
# app/config.py
from dataclasses import dataclass
from typing import Literal
import os
from dotenv import load_dotenv

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

@dataclass(frozen=True)
class Config:
    """Application configuration."""

    # Discord設定
    discord_bot_token: str
    discord_command_prefix: str = "!"

    # データベース設定
    database_url: str = "sqlite+aiosqlite:///./bot.db"

    # ログ設定
    log_level: LogLevel = "INFO"

    # アプリケーション設定
    debug: bool = False

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        # .env.local を優先的に読み込み
        if os.path.exists(".env.local"):
            load_dotenv(".env.local", override=True)
        else:
            load_dotenv()

        discord_token = os.getenv("DISCORD_BOT_TOKEN")
        if not discord_token:
            raise ValueError("DISCORD_BOT_TOKEN is required")

        return cls(
            discord_bot_token=discord_token,
            discord_command_prefix=os.getenv("DISCORD_COMMAND_PREFIX", "!"),
            database_url=os.getenv(
                "DATABASE_URL",
                "sqlite+aiosqlite:///./bot.db"
            ),
            log_level=os.getenv("LOG_LEVEL", "INFO"),  # type: ignore[arg-type]
            debug=os.getenv("DEBUG", "false").lower() == "true",
        )

# app/__main__.py
from app.config import Config

async def main() -> None:
    config = Config.from_env()
    setup_logging(level=config.log_level)
    await init_db(config.database_url)

    bot = commands.Bot(command_prefix=config.discord_command_prefix)
    # ...
    await bot.start(config.discord_bot_token)
```

**推定工数**: 2-3時間

---

## 📊 優先度別工数サマリー

| 優先度   | 項目数     | 合計推定工数  |
| -------- | ---------- | ------------- |
| 🔴 高    | 3項目      | 5-8時間       |
| 🟡 中    | 5項目      | 20-27時間     |
| 🟢 低    | 4項目      | 7-11時間      |
| **合計** | **12項目** | **32-46時間** |

---

## 🎯 推奨実装順序

### フェーズ1: 緊急対応（1週間以内）

1. メールアドレス検証の追加（2時間）
2. データベース一意制約エラーハンドリング（3時間）
3. 未追跡ファイルのGit追加（5分）

### フェーズ2: 品質向上（2-3週間）

4. ORMタイムスタンプフィールド修正（3時間）
5. Discord コマンドのセキュリティ対策（4時間）
6. テストカバレッジ向上（6時間）

### フェーズ3: リファクタリング（1-2ヶ月）

7. Domain-ORM マッピング改善（5時間）
8. 設定管理の一元化（3時間）
9. ログ設定の一元管理（2時間）

### フェーズ4: アーキテクチャ改善（長期）

10. データベースサービスのDI化（4時間）
11. Mediator自動登録の明示化（8時間）
12. テスト並列実行対応（3時間）

---

## 📝 備考

- このドキュメントは定期的に見直し、更新すること
- 新しい課題が発見された場合は、このドキュメントに追記すること
- 各項目の対応完了後は、完了日とコミットハッシュを記録すること

**レビュー実施者**: Claude Code
**レビュー日時**: 2025-11-26
**プロジェクトバージョン**: 0.1.0
