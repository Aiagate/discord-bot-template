# アーキテクチャ設計ドキュメント

最終更新日: 2025-11-28

このドキュメントは、Discord Bot テンプレートのアーキテクチャ設計と実装パターンを詳細に説明します。

---

## 📐 アーキテクチャ概要

このプロジェクトは **クリーンアーキテクチャ（Clean Architecture）** に基づいて設計されています。

### レイヤー構造

```
┌─────────────────────────────────────────┐
│  Presentation Layer                     │  外部インターフェース
│  (Discord Bot, Cogs)                    │  - ユーザーからの入力受付
│  - app/__main__.py                      │  - 出力のフォーマット
│  - app/cogs/*.py                        │
├─────────────────────────────────────────┤
│  Application Layer                      │  ユースケース
│  (Use Cases, Mediator)                  │  - ビジネスフロー制御
│  - app/usecases/                        │  - DTOでの入出力
│  - app/mediator.py                      │  - Result型でのエラーハンドリング
├─────────────────────────────────────────┤
│  Domain Layer                           │  ビジネスルール
│  (Aggregates, Entities, Value Objects)  │  - 純粋なPythonオブジェクト
│  - app/domain/aggregates/               │  - フレームワーク非依存
│  - app/domain/repositories/             │  - ビジネスロジックの検証
├─────────────────────────────────────────┤
│  Infrastructure Layer                   │  技術的詳細
│  (Database, ORM, External Services)     │  - データベースアクセス
│  - app/infrastructure/database.py       │  - 外部API呼び出し
│  - app/infrastructure/orm_models/       │  - ファイルシステムアクセス
│  - app/infrastructure/repositories/     │
│  - app/infrastructure/unit_of_work.py   │
│  - app/container.py (DI)                │
└─────────────────────────────────────────┘
```

### 依存関係の方向

```
Presentation ──▶ Application ──▶ Domain ◀── Infrastructure
                                    ▲
                                    │
                            依存性の逆転原理
                          (Dependency Inversion)
```

**重要な原則**:

- 上位層は下位層に依存可能
- **下位層は上位層に依存してはならない**
- **ドメイン層は最も独立しており、他のどの層にも依存しない**
- インフラ層はドメイン層のインターフェースに依存（依存性逆転）

---

## 🏗️ 各レイヤーの詳細

### 1. Domain Layer（ドメイン層）

**責務**: ビジネスルールとビジネスロジックの実装

**特徴**:

- 純粋なPythonコード（dataclass、関数）
- フレームワーク非依存
- データベース、Web、UIに関する知識を持たない
- 他のどのレイヤーにも依存しない

#### 構成要素

##### 1.1 Aggregates（集約）

`app/domain/aggregates/user.py`:

```python
from dataclasses import dataclass

@dataclass
class User:
    """User aggregate root."""

    id: int
    name: str
    email: str

    def __post_init__(self) -> None:
        # ドメインルールの検証
        if not self.name:
            raise ValueError("User name cannot be empty.")

    def change_email(self, new_email: str) -> "User":
        """ビジネスロジック: メールアドレス変更"""
        self.email = new_email
        return self
```

**ポイント**:

- ビジネスルールを `__post_init__` で検証
- イミュータブル（変更メソッドは新しいインスタンスを返す）
- リッチドメインモデル（データだけでなく振る舞いを持つ）

##### 1.2 Repository Interfaces（リポジトリインターフェース）

`app/repository.py`:

```python
from abc import ABC, abstractmethod
from app.core.result import Result

class IRepository[T](ABC):
    """基本リポジトリインターフェース（追加・削除操作）"""

    @abstractmethod
    async def add(self, entity: T) -> Result[T, RepositoryError]:
        pass

    @abstractmethod
    async def delete(self, entity: T) -> Result[None, RepositoryError]:
        pass


class IRepositoryWithId[T, K](IRepository[T], ABC):
    """ID検索機能付きリポジトリインターフェース"""

    @abstractmethod
    async def get_by_id(self, id: K) -> Result[T, RepositoryError]:
        pass
```

**ポイント**:

- ドメイン層でインターフェースを定義
- 実装はインフラ層が担当（依存性逆転）
- Result型で型安全なエラーハンドリング

**設計判断: Protocol から ABC への移行**:

当初は `Protocol` ベースの設計を採用していましたが、DI（依存性注入）による
インターフェース分離が実現されているため、`Protocol` の構造的型付けの柔軟性は
不要であることが判明しました。

`ABC` ベースの明示的継承により、以下の利点が得られます:
- 型安全性の向上（クラス定義時にエラー検出）
- IDEサポートの改善（自動補完、リファクタリング）
- 開発者の意図の明確化
- インターフェースと実装の乖離防止

なお、`IValueObject` などのドメイン層インターフェースは、ランタイム型チェックが
必要なため、引き続き `Protocol` を使用します。

##### 1.3 Result Type（結果型）

`app/core/result.py`:

```python
@dataclass(frozen=True)
class Ok[T]:
    """成功結果"""
    value: T

@dataclass(frozen=True)
class Err[E]:
    """失敗結果"""
    error: E

Result = Ok[T] | Err[E]
```

**ポイント**:

- Rust の Result型にインスパイア
- 例外ではなく値でエラーを表現
- パターンマッチングで処理分岐

**使用例**:

```python
result = await user_repo.get_by_id(user_id)

match result:
    case Ok(user):
        print(f"Found: {user.name}")
    case Err(error):
        print(f"Error: {error.message}")
```

---

### 2. Application Layer（アプリケーション層）

**責務**: ユースケースの実装、ビジネスフローの制御

**特徴**:

- ドメインオブジェクトを操作してビジネスフローを実現
- DTOで入出力を定義
- トランザクション境界の管理（Unit of Work）

#### 構成要素

##### 2.1 Use Cases（ユースケース）

各ユースケースは以下の3要素で構成:

1. **Query/Command クラス**: リクエスト
2. **Result クラス**: レスポンス
3. **Handler クラス**: 処理ロジック

**重要な設計原則**: Create系のユースケースは作成したエンティティのIDのみを返し、詳細情報の取得はGet系のユースケースに委譲します。これにより以下のSOLID原則がより厳密に守られます：

- **単一責任の原則（SRP）**: Createは「エンティティの作成」、Getは「エンティティの詳細取得」という明確な単一責任を持つ
- **開放閉鎖の原則（OCP）**: 表示ロジックをGetに一元化することで、表示形式の変更時に既存のCreateコードを変更する必要がない
- **インターフェース分離の原則（ISP）**: Createは最小限の情報（ID）のみを返し、クライアントに不要な情報を公開しない

`app/usecases/users/get_user.py`:

```python
# 1. Query（リクエスト）
class GetUserQuery(Request[Result[GetUserResult, UseCaseError]]):
    def __init__(self, user_id: int) -> None:
        self.user_id = user_id

# 2. Result（レスポンス）
class GetUserResult:
    def __init__(self, user: UserDTO) -> None:
        self.user = user

# 3. Handler（処理ロジック）
class GetUserHandler(RequestHandler[GetUserQuery, Result[GetUserResult, UseCaseError]]):
    @inject
    def __init__(self, uow: IUnitOfWork) -> None:
        self._uow = uow

    async def handle(self, request: GetUserQuery) -> Result[GetUserResult, UseCaseError]:
        async with self._uow:
            user_repo = self._uow.GetRepository(User, int)
            user_result = await user_repo.get_by_id(request.user_id)

            match user_result:
                case Ok(user):
                    user_dto = UserDTO(
                        id=user.id,
                        name=user.name,
                        email=user.email
                    )
                    return Ok(GetUserResult(user_dto))
                case Err(repo_error):
                    uc_error = UseCaseError(
                        type=ErrorType.NOT_FOUND,
                        message=repo_error.message
                    )
                    return Err(uc_error)
```

**ポイント**:

- **CQRS パターン**: Query（読み取り）と Command（書き込み）を分離
- **DTO（Data Transfer Object）**: プレゼンテーション層との境界
- **依存性注入**: `@inject` デコレータで IUnitOfWork を注入
- **トランザクション**: `async with self._uow` でトランザクション管理

`app/usecases/users/create_user.py` (Command例):

```python
# 1. Command（リクエスト）
class CreateUserCommand(Request[Result[CreateUserResult, UseCaseError]]):
    def __init__(self, name: str, email: str) -> None:
        self.name = name
        self.email = email

# 2. Result（レスポンス）- IDのみを返す
class CreateUserResult:
    def __init__(self, user_id: str) -> None:
        self.user_id = user_id

# 3. Handler（処理ロジック）
class CreateUserHandler(RequestHandler[CreateUserCommand, Result[CreateUserResult, UseCaseError]]):
    @inject
    def __init__(self, uow: IUnitOfWork) -> None:
        self._uow = uow

    async def handle(self, request: CreateUserCommand) -> Result[CreateUserResult, UseCaseError]:
        # エンティティ作成
        user = User(id=UserId.generate(), name=request.name, email=Email.from_primitive(request.email))

        async with self._uow:
            user_repo = self._uow.GetRepository(User)
            save_result = await user_repo.add(user)

            match save_result:
                case Ok(saved_user):
                    # IDのみを返す
                    return Ok(CreateUserResult(saved_user.id.to_primitive()))
                case Err(repo_error):
                    return Err(UseCaseError(type=ErrorType.UNEXPECTED, message=repo_error.message))
```

**Createの設計パターン**: Create系のユースケースはIDのみを返します。プレゼンテーション層（Cog）では、返されたIDを使ってGetユースケースを呼び出すことで、詳細情報を取得します：

```python
# app/cogs/users_cog.py
@users.command(name="create")
async def users_create(self, ctx: commands.Context[commands.Bot], name: str, email: str) -> None:
    # 1. Createを実行してIDを取得
    command = CreateUserCommand(name=name, email=email)
    result = await Mediator.send_async(command)

    match result:
        case Ok(ok_value):
            # 2. 返されたIDでGetを実行
            query = GetUserQuery(user_id=ok_value.user_id)
            get_result = await Mediator.send_async(query)

            match get_result:
                case Ok(get_ok_value):
                    # 3. 結果を表示（表示ロジックがGetに一元化される）
                    message = f"User Created:\nID: {get_ok_value.user.id}\nName: {get_ok_value.user.name}\n..."
                    await ctx.send(content=message)
```

この設計により：
- Createは「作成してIDを返す」という単一責任に専念
- Getは「詳細情報の取得と形式化」という単一責任に専念
- 結果の表示形式を変更する場合、Getの実装のみを変更すればよい（OCP）
- テストが容易（各ユースケースを独立してテスト可能）

##### 2.2 Mediator Pattern（メディエーターパターン）

`app/mediator.py`:

```python
class Mediator:
    """CQRS-style mediator for request/response."""

    @classmethod
    async def send_async[TResponse](
        cls, request: Request[TResponse]
    ) -> TResponse:
        """Send request to handler and get response."""
        handler = cls._get_handler(type(request))
        return await handler.handle(request)
```

**利点**:

- プレゼンテーション層とアプリケーション層の疎結合
- ハンドラーの自動登録（メタクラス使用）
- 一貫したリクエスト/レスポンスパターン

**使用例**:

```python
# Discord Cog から
query = GetUserQuery(user_id=123)
result = await Mediator.send_async(query)
```

##### 2.3 DTOs（Data Transfer Objects）

`app/usecases/users/user_dto.py`:

```python
@dataclass(frozen=True)
class UserDTO:
    """User Data Transfer Object."""
    id: int
    name: str
    email: str
```

**ポイント**:

- イミュータブル（`frozen=True`）
- ドメイン集約とは別物（表示用）
- プレゼンテーション層に公開する情報のみ含む

---

### 3. Infrastructure Layer（インフラストラクチャ層）

**責務**: 技術的な詳細の実装（DB、外部API等）

**特徴**:

- ドメイン層のインターフェースを実装
- ORM、データベース接続、外部サービスとの通信
- ドメイン集約とORMモデルの変換

#### 構成要素

##### 3.1 ORM Models

`app/infrastructure/orm_models/user_orm.py`:

```python
from sqlmodel import SQLModel, Field

class UserORM(SQLModel, table=True):
    """User table ORM model."""
    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(max_length=255, index=True)
    email: str = Field(max_length=255, unique=True, index=True)
    created_at: str | None = Field(default=None)
    updated_at: str | None = Field(default=None)
```

**ポイント**:

- **ドメイン集約とは完全に分離**
- データベーステーブルの表現
- SQLAlchemy の制約・インデックスを定義

##### 3.2 Generic Repository

`app/infrastructure/repositories/generic_repository.py`:

```python
class GenericRepository[T, K](IRepositoryWithId[T, K]):
    """汎用リポジトリ実装 - IRepositoryWithId[T, K]を明示的に実装"""

    def __init__(
        self,
        session: AsyncSession,
        entity_type: type[T],
        key_type: type[K] | None
    ) -> None:
        self._session = session
        self._entity_type = entity_type
        self._key_type = key_type
        self._orm_type = ORMMappingRegistry.get_orm_type(entity_type)

    async def get_by_id(self, id: K) -> Result[T, RepositoryError]:
        statement = select(self._orm_type).where(self._orm_type.id == id)
        result = await self._session.execute(statement)
        orm_instance = result.scalar_one_or_none()

        if orm_instance is None:
            return Err(RepositoryError(...))

        # ORM → Domain 自動変換
        return Ok(ORMMappingRegistry.from_orm(orm_instance))
```

**ポイント**:

- 型安全な汎用実装（Generics使用）
- ORM ↔ Domain の変換を担当
- Result型でエラーハンドリング

**自動変換機構**:

ドメイン集約とORMモデル間の変換は、`IValueObject` Protocolを活用して自動的に行われます:

```python
def entity_to_orm_dict(entity: Any) -> dict[str, Any]:
    """ドメインエンティティをORM用辞書に変換

    - dataclassのフィールドを走査
    - IValueObjectフィールドはto_primitive()で変換
    - プリミティブ型はそのまま使用
    """
    if not is_dataclass(entity):
        raise TypeError(f"Expected dataclass, got {type(entity).__name__}")

    result: dict[str, Any] = {}
    for field in fields(entity):
        field_value = getattr(entity, field.name)
        if isinstance(field_value, IValueObject):
            result[field.name] = field_value.to_primitive()
        else:
            result[field.name] = field_value

    return result


def orm_to_entity(orm_instance: SQLModel, entity_type: type[T]) -> T:
    """ORMモデルをドメインエンティティに変換

    - 型アノテーションを取得
    - from_primitive()メソッドを持つ型はValue Objectとして変換
    - プリミティブ型はそのまま使用
    """
    type_hints = get_type_hints(entity_type)
    kwargs: dict[str, Any] = {}

    for field in fields(entity_type):
        field_type = type_hints[field.name]
        orm_value = getattr(orm_instance, field.name, None)

        if hasattr(field_type, "from_primitive"):
            if orm_value is None and field.name == "id":
                kwargs[field.name] = field_type.generate()
            else:
                kwargs[field.name] = field_type.from_primitive(orm_value)
        else:
            kwargs[field.name] = orm_value

    return entity_type(**kwargs)
```

**利点**:

- **型安全**: 型アノテーションベースで自動変換
- **保守性向上**: 新しいValue Objectを追加しても変換コード不要
- **依存性逆転**: ドメイン層がインフラ層に依存しない
- **DRY原則**: 変換ロジックの重複を排除

##### 3.3 Unit of Work Pattern

`app/infrastructure/unit_of_work.py`:

```python
class SQLAlchemyUnitOfWork(IUnitOfWork):
    """トランザクション境界を管理"""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory
        self._session: AsyncSession | None = None
        self._repositories: dict[tuple[type, type], Any] = {}

    def GetRepository[T, K](
        self, entity_type: type[T], key_type: type[K]
    ) -> IRepository[T, K]:
        """リポジトリの取得（キャッシュ付き）"""
        cache_key = (entity_type, key_type)

        if cache_key in self._repositories:
            return self._repositories[cache_key]

        repository = GenericRepository[T, K](
            self._session, entity_type, key_type
        )
        self._repositories[cache_key] = repository
        return repository

    async def __aenter__(self) -> "SQLAlchemyUnitOfWork":
        self._session = self._session_factory()
        await self._session.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type is None:
            await self.commit()  # 成功時はコミット
        else:
            await self.rollback()  # 例外時はロールバック

        await self._session.__aexit__(exc_type, exc_val, exc_tb)
        self._repositories.clear()
```

**ポイント**:

- **トランザクション境界の明確化**
- リポジトリのキャッシュ（同一トランザクション内で再利用）
- 自動コミット/ロールバック（コンテキストマネージャー）

**使用例**:

```python
async with self._uow:  # トランザクション開始
    user_repo = self._uow.GetRepository(User, int)
    result = await user_repo.save(user)
    # コンテキスト終了時に自動コミット
```

##### 3.4 Dependency Injection Container

`app/container.py`:

```python
from injector import Binder, Module, singleton

class AppModule(Module):
    """DIコンテナの設定"""

    def configure(self, binder: Binder) -> None:
        # セッションファクトリをシングルトンでバインド
        binder.bind(
            async_sessionmaker[AsyncSession],
            to=get_session_factory(),
            scope=singleton,
        )

        # UnitOfWork をリクエストごとに生成
        binder.bind(
            IUnitOfWork,
            to=lambda: SQLAlchemyUnitOfWork(get_session_factory()),
        )
```

**ポイント**:

- `injector` ライブラリを使用
- シングルトンとリクエストスコープの使い分け
- テスト時のモック注入が容易

##### 3.5 ORM Mapping Registry

`app/infrastructure/orm_registry.py`:

```python
def init_orm_mappings() -> None:
    """Initialize all ORM mappings."""
    register_orm_mapping(User, UserORM)
    register_orm_mapping(Team, TeamORM)

# Auto-register on import
init_orm_mappings()
```

**ポイント**:

- **集中管理**: すべてのマッピングを一箇所で管理
- **自動登録**: モジュールインポート時に自動実行
- **拡張容易**: 新しい集約追加時はここに1行追加するだけ
- **明示的**: どの集約がマッピングされているか一目瞭然

**使用方法**:

```python
# container.py で初期化
from app.infrastructure.orm_registry import init_orm_mappings

def configure(binder: Binder) -> None:
    init_orm_mappings()  # マッピング初期化
    # ... 他のバインディング
```

**利点**:

- Domain層からInfrastructure層への依存が完全に削除される
- 新しいAggregateを追加する際の作業が1行で完結
- 自動変換機構により、変換コードの記述が不要

---

### 4. Presentation Layer（プレゼンテーション層）

**責務**: ユーザーインターフェース、入出力の制御

**特徴**:

- Discord Bot のコマンド実装
- 入力の受付とバリデーション
- 出力のフォーマット

#### 構成要素

##### 4.1 Discord Bot Entry Point

`app/__main__.py`:

```python
async def main() -> None:
    # 環境変数読み込み
    if os.path.exists(".env.local"):
        load_dotenv(".env.local", override=True)
    else:
        load_dotenv()

    # データベース初期化
    database_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./bot.db")
    await init_db(database_url)

    # Bot作成
    bot = commands.Bot(command_prefix="!", intents=intents)

    # Cog読み込み
    await bot.load_extension("app.cogs.users_cog")

    # Bot起動
    token = os.getenv("DISCORD_BOT_TOKEN")
    await bot.start(token)
```

##### 4.2 Discord Cogs

`app/cogs/users_cog.py`:

```python
class UsersCog(commands.Cog):
    """User management commands."""

    @commands.group(name="users")
    async def users(self, ctx: commands.Context[commands.Bot]) -> None:
        """User commands group."""
        if ctx.invoked_subcommand is None:
            await ctx.send("Use: !users get <id> or !users create <name> <email>")

    @users.command(name="get")
    async def users_get(
        self, ctx: commands.Context[commands.Bot], user_id: int
    ) -> None:
        """Get user by ID."""
        query = GetUserQuery(user_id=user_id)
        result = await Mediator.send_async(query)

        match result:
            case Ok(ok_value):
                user = ok_value.user
                await ctx.send(
                    f"**User #{user.id}**\n"
                    f"Name: {user.name}\n"
                    f"Email: {user.email}"
                )
            case Err(err_value):
                await ctx.send(f"❌ Error: {err_value.message}")
```

**ポイント**:

- Mediator経由でユースケースを呼び出し
- Result型でエラーハンドリング
- Discord用のメッセージフォーマット

---

## 🔄 データフロー

### Query（読み取り）のフロー

```
1. Discord User
   ↓ !users get 123
2. UsersCog.users_get()
   ↓ GetUserQuery(user_id=123)
3. Mediator.send_async()
   ↓
4. GetUserHandler.handle()
   ↓ IUnitOfWork
5. SQLAlchemyUnitOfWork.GetRepository()
   ↓
6. GenericRepository.get_by_id()
   ↓ SELECT * FROM users WHERE id = 123
7. Database (SQLite/PostgreSQL)
   ↓ UserORM
8. orm_to_domain()
   ↓ User (Domain)
9. User → UserDTO
   ↓ Ok(GetUserResult(UserDTO))
10. Match result → format message
    ↓
11. Discord User (receives formatted message)
```

### Command（書き込み）のフロー

```
1. Discord User
   ↓ !users create "Alice" "alice@example.com"
2. UsersCog.users_create()
   ↓ CreateUserCommand(name="Alice", email="alice@...")
3. Mediator.send_async()
   ↓
4. CreateUserHandler.handle()
   ↓ User(id=UserId.generate(), name="Alice", email="alice@...")
5. Domain validation (__post_init__)
   ↓
6. IUnitOfWork
   ↓
7. GenericRepository.add()
   ↓ entity_to_orm_dict()
8. UserORM
   ↓ INSERT INTO users ...
9. Database
   ↓ Commit transaction
10. Ok(CreateUserResult(user_id="01HQXYZ..."))
    ↓ IDのみを返す
11. UsersCog.users_create()
    ↓ GetUserQuery(user_id="01HQXYZ...")
12. Mediator.send_async()
    ↓
13. GetUserHandler.handle()
    ↓ GenericRepository.get_by_id()
14. Database
    ↓ SELECT * FROM users WHERE id = '01HQXYZ...'
15. UserORM → User (Domain)
    ↓ orm_to_entity()
16. User → UserDTO
    ↓ Ok(GetUserResult(UserDTO))
17. UsersCog formats message
    ↓
18. Discord User (receives formatted success message)
```

**重要**: Create操作は作成したエンティティのIDのみを返します。詳細情報の取得は必ずGet操作を経由することで、表示ロジックが一元化され、SOLID原則（特にSRPとOCP）が守られます。

---

## 🎯 設計原則

### 1. SOLID原則の適用

#### Single Responsibility Principle（単一責任の原則）

- 各クラスは単一の責任のみを持つ
- 例: `GetUserHandler` はユーザー取得のみ、`GenericRepository` はデータアクセスのみ

#### Open/Closed Principle（開放閉鎖の原則）

- 拡張に対して開いている、修正に対して閉じている
- 例: 新しい集約を追加する際、既存コードを変更せずに済む（Generic Repository）

#### Liskov Substitution Principle（リスコフの置換原則）

- 派生型は基本型と置換可能
- 例: `SQLAlchemyUnitOfWork` は `IUnitOfWork` と置換可能

#### Interface Segregation Principle（インターフェース分離の原則）

- クライアントは使用しないインターフェースに依存すべきでない
- 例: `IRepository` は最小限のメソッドのみ定義

#### Dependency Inversion Principle（依存性逆転の原則）

- 上位モジュールは下位モジュールに依存すべきでない、両方とも抽象に依存すべき
- 例: ユースケースは `IUnitOfWork` に依存、具体的な実装には依存しない

### 2. その他の設計原則

#### DRY（Don't Repeat Yourself）

- Generic Repository で共通処理を一元化
- Mediator パターンでリクエスト/レスポンス処理を統一

#### YAGNI（You Aren't Gonna Need It）

- 現在必要な機能のみ実装
- 過度な抽象化を避ける

#### Separation of Concerns（関心の分離）

- 各レイヤーが明確な責務を持つ
- ドメインロジックとインフラロジックを完全に分離

---

## 🧪 テスト戦略

### テストピラミッド

```
      ┌──────────┐
      │   E2E    │  少数（統合テスト）
      ├──────────┤
      │   統合    │  中程度（ユースケーステスト）
      ├──────────┤
      │ ユニット  │  多数（ドメイン・リポジトリテスト）
      └──────────┘
```

### 1. ユニットテスト

**対象**: ドメイン層、リポジトリ層

`tests/domain/aggregates/test_user.py`:

```python
@pytest.mark.anyio
async def test_create_user_with_empty_name_raises_error() -> None:
    with pytest.raises(ValueError, match="User name cannot be empty"):
        User(id=1, name="", email="test@example.com")
```

**特徴**:

- 高速（0.44秒で13テスト）
- インメモリSQLite使用
- 外部依存なし

### 2. 統合テスト

**対象**: ユースケース層

`tests/usecases/users/test_get_user.py`:

```python
@pytest.mark.anyio
async def test_get_user_handler(uow: IUnitOfWork) -> None:
    # Setup
    async with uow:
        repo = uow.GetRepository(User, int)
        user = User(id=0, name="Bob", email="bob@example.com")
        save_result = await repo.save(user)

    # Execute
    handler = GetUserHandler(uow)
    result = await handler.handle(GetUserQuery(user_id=1))

    # Assert
    assert isinstance(result, Ok)
    assert result.value.user.name == "Bob"
```

**特徴**:

- データベースを含む
- トランザクション動作の検証
- Result型の動作確認

### 3. E2Eテスト（TODO）

**対象**: プレゼンテーション層～インフラ層の全体

- Discord Bot の実際のコマンド実行
- モックDiscordコンテキストを使用

---

## 📦 依存関係管理

### プロダクション依存関係

```toml
[project.dependencies]
aiosqlite = ">=0.21.0"     # 非同期SQLite
alembic = ">=1.17.2"       # DBマイグレーション
discord-py = ">=2.5.2"     # Discord API
injector = ">=0.22.0"      # 依存性注入
python-dotenv = ">=1.2.1"  # 環境変数管理
sqlmodel = ">=0.0.24"      # ORM（SQLAlchemy + Pydantic）
```

### 開発依存関係

```toml
[dependency-groups.dev]
anyio = ">=4.11.0"         # 非同期テストサポート
pre-commit = ">=4.5.0"     # Git フック
pyright = ">=1.1.407"      # 型チェッカー
pytest = ">=8.3.5"         # テストフレームワーク
pytest-asyncio = ">=1.3.0" # 非同期テスト
pytest-cov = ">=7.0.0"     # カバレッジ測定
pytest-mock = ">=3.14.0"   # モック
ruff = ">=0.14.6"          # リンター・フォーマッター
```

---

## 🚀 拡張方法

### 新しい集約の追加

1. **ドメイン集約を作成**

```python
# app/domain/aggregates/guild.py
@dataclass
class Guild:
    id: int
    name: str
    owner_id: int
```

2. **ORMモデルを作成**

```python
# app/infrastructure/orm_models/guild_orm.py
class GuildORM(SQLModel, table=True):
    __tablename__ = "guilds"
    id: int | None = Field(default=None, primary_key=True)
    name: str
    owner_id: int
```

3. **マッピングを追加**

```python
# app/infrastructure/repositories/generic_repository.py
DOMAIN_TO_ORM_MAP: dict[type, type[SQLModel]] = {
    User: UserORM,
    Guild: GuildORM,  # 追加
}
```

4. **ユースケースを作成**

```python
# app/usecases/guilds/get_guild.py
class GetGuildQuery(Request[Result[GetGuildResult, UseCaseError]]):
    pass

class GetGuildHandler(RequestHandler[...]):
    pass
```

5. **Cogを作成**

```python
# app/cogs/guilds_cog.py
class GuildsCog(commands.Cog):
    @commands.command()
    async def guild_info(self, ctx):
        pass
```

### データベースマイグレーション

```bash
# スキーマ変更後、マイグレーションを生成
uv run alembic revision --autogenerate -m "Add guilds table"

# マイグレーション適用
uv run alembic upgrade head
```

---

## 📚 参考資料

- [Clean Architecture (Robert C. Martin)](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Domain-Driven Design](https://www.domainlanguage.com/ddd/)
- [CQRS Pattern](https://martinfowler.com/bliki/CQRS.html)
- [Repository Pattern](https://martinfowler.com/eaaCatalog/repository.html)
- [Unit of Work Pattern](https://martinfowler.com/eaaCatalog/unitOfWork.html)

---

**ドキュメント作成者**: Claude Code
**作成日**: 2025-11-26
**バージョン**: 1.0
