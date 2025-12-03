# Result型ガイド

このドキュメントでは、`app.core.result`で提供される`Result`型の設計思想と実践的な使用方法について解説します。

## 📚 目次

1. [なぜResult型なのか](#なぜresult型なのか)
2. [Result型の基本構造](#result型の基本構造)
3. [使用方法](#使用方法)
4. [高度な使用パターン](#高度な使用パターン)
5. [ベストプラクティス](#ベストプラクティス)

---

## なぜResult型なのか

### 設計の動機

Pythonには例外処理機構がありますが、以下の課題があります：

1. **暗黙的なエラーフロー**: 関数シグネチャを見ても、どのような例外が発生するか分からない
2. **エラーハンドリングの強制不足**: 例外処理を書き忘れても、実行時まで分からない
3. **型チェッカーの限界**: `mypy`や`pyright`は例外の存在を型システムで追跡できない

```python
# 従来の例外ベース - 問題点
def get_user(user_id: int) -> User:  # どんなエラーが起きる？
    if user_id < 0:
        raise ValueError("Invalid user ID")  # 呼び出し側は知らない
    # ...
```

### Result型による解決

`Result`型は、**成功と失敗を型で表現**することで、これらの問題を解決します：

```python
# Result型 - 利点
def get_user(user_id: int) -> Result[User, UseCaseError]:
    # ↑ 型シグネチャが「成功ならUser、失敗ならUseCaseErrorを返す」と明示
    if user_id < 0:
        return Err(UseCaseError(type=ErrorType.VALIDATION_ERROR, message="Invalid ID"))
    return Ok(user)
```

**利点：**
- ✅ エラーが型システムで追跡可能
- ✅ 呼び出し側で`Ok`と`Err`の両方を処理する必要がある（型チェッカーが警告）
- ✅ Railway-oriented programmingによる安全なエラー伝播
- ✅ Rustの`Result`型に影響を受けた、実績のあるパターン

---

## Result型の基本構造

### 型定義

```python
Result = Ok[T] | Err[E]
```

- `Ok[T]`: 成功を表し、値`T`を保持
- `Err[E]`: 失敗を表し、エラー`E`を保持

### データ構造

```python
@dataclass(frozen=True)
class Ok[T]:
    value: T

@dataclass(frozen=True)
class Err[E]:
    error: E
```

**不変性（`frozen=True`）の理由：**
- Result値は一度作成されたら変更されない
- 関数型プログラミングの原則に従い、副作用を最小化
- スレッドセーフ性の向上

---

## 使用方法

### 1. 基本：パターンマッチング

Python 3.10以降の`match`文を使用します：

```python
from app.core.result import Result, Ok, Err

def find_user(user_id: int) -> Result[str, str]:
    if user_id == 1:
        return Ok("Alice")
    return Err("User not found")

# 使用例
result = find_user(1)

match result:
    case Ok(user_name):
        print(f"Found: {user_name}")
    case Err(error_message):
        print(f"Error: {error_message}")
```

**なぜmatch文？**
- 構造的パターンマッチングにより、値の取り出しが簡潔
- すべてのケースを網羅することを型チェッカーが確認
- 読みやすく、バグを減らせる

### 2. 型ガード：`is_ok`と`is_err`

型ナローイングが必要な場合に使用：

```python
from app.core.result import is_ok, is_err

result = find_user(1)

if is_ok(result):
    # この中では result は Ok[str] 型
    print(result.value)
elif is_err(result):
    # この中では result は Err[str] 型
    print(result.error)
```

**なぜ型ガード？**
- `isinstance`よりも意図が明確
- `TypeGuard`により型チェッカーが型を正しく推論

### 3. Railway-oriented programming

#### `map`: 成功値の変換

```python
result = Ok(5)
doubled = result.map(lambda x: x * 2)
# -> Ok(10)

error = Err("failed")
doubled = error.map(lambda x: x * 2)
# -> Err("failed") - エラーは素通り
```

**なぜmapメソッド？**
- エラーチェックを書かずに値を変換できる
- エラーは自動的に伝播（Railway pattern）
- チェーン可能で読みやすい

#### `and_then`: 失敗しうる変換

```python
def validate_positive(x: int) -> Result[int, str]:
    if x > 0:
        return Ok(x)
    return Err("Must be positive")

result = Ok(5).and_then(validate_positive)
# -> Ok(5)

result = Ok(-3).and_then(validate_positive)
# -> Err("Must be positive")
```

**なぜand_then？**
- `map`との違い：変換関数自体が`Result`を返す場合に使用
- ネストした`Result[Result[T, E], E]`を防ぐ（flatMap相当）
- 複数の検証を簡潔に連鎖できる

### 4. `unwrap`: 値の取り出し

```python
result = Ok(42)
value = result.unwrap()  # -> 42

error_result = Err(UseCaseError(...))
value = error_result.unwrap()  # -> 例外が発生
```

**いつunwrapを使う？**
- ✅ 失敗が絶対にありえない場合
- ✅ テストコード内
- ❌ 本番コード内での多用は避ける（例外に戻ってしまう）

---

## 高度な使用パターン

### 1. 複数のResultの集約：`combine`

複数の`Result`を一つにまとめます：

```python
from app.core.result import combine

results = [Ok(1), Ok(2), Ok(3)]
combined = combine(results)
# -> Ok((1, 2, 3))  # タプルで返される

results = [Ok(1), Err("error"), Ok(3)]
combined = combine(results)
# -> Err("error")  # 最初のエラーを返す
```

**なぜcombine？**
- 複数の独立した処理を並行実行後、結果をまとめる際に便利
- 一つでも失敗したら全体が失敗（All or Nothing）
- **型安全性**: `combine`は2つのパターンをサポート
  - 同じ型: `combine[T, E](results: Sequence[Result[T, E]]) -> Result[tuple[T, ...], E]`
  - 異なる型: `combine[T1, T2, E](results: tuple[Result[T1, E], Result[T2, E]]) -> Result[tuple[T1, T2], E]`
  - すべての`Result`のエラー型`E`は同じである必要がある

**使用例：複数のバリデーション（同じ型）**

```python
def validate_user_data(
    name: str,
    email: str,
    age: int
) -> Result[tuple[str, str, int], UseCaseError]:
    name_result = validate_name(name)
    email_result = validate_email(email)
    age_result = validate_age(age)

    combined = combine([name_result, email_result, age_result])

    match combined:
        case Ok((valid_name, valid_email, valid_age)):
            return Ok((valid_name, valid_email, valid_age))
        case Err(error):
            return Err(error)  # 最初のエラーを返す
```

#### 異なる型の組み合わせ（ヘテロジニアス型）

`combine`は異なる型の`Result`も扱えます。この場合、**タプル**で渡します：

```python
# 実例：ユーザーIDとメールアドレスのバリデーション
user_id: Result[int, UseCaseError] = validate_user_id("123")
email: Result[str, UseCaseError] = validate_email("user@example.com")

# タプルで渡すと、異なる型を組み合わせられる
combined = combine((user_id, email))
# 型: Result[tuple[int, str], UseCaseError]

match combined:
    case Ok((uid, mail)):
        # uid: int（int型として推論される）
        # mail: str（str型として推論される）
        return create_user(uid, mail)
    case Err(error):
        return Err(error)
```

**使用例：複数フィールドのバリデーション**

```python
def validate_profile(
    name: str, age: int, email: str, is_active: bool
) -> Result[ValidatedProfile, UseCaseError]:
    # 各フィールドを個別に検証
    name_result = validate_name(name)
    age_result = validate_age(age)
    email_result = validate_email(email)
    active_result = validate_boolean(is_active)

    # 4つの異なる型を組み合わせる
    combined = combine((name_result, age_result, email_result, active_result))

    match combined:
        case Ok((valid_name, valid_age, valid_email, valid_active)):
            return Ok(ValidatedProfile(
                name=valid_name,    # str
                age=valid_age,      # int
                email=valid_email,  # str
                active=valid_active # bool
            ))
        case Err(error):
            return Err(error)
```

**メリット：**
- 各要素の型が保持される（型安全性）
- 最大10個まで対応
- Pyrightによるコンパイル時の型チェックが機能
- パターンマッチングとの親和性が高い

**同じ型の場合**:
```python
# 同じ型の場合はリストまたはタプルで渡せます
results = [Ok(1), Ok(2), Ok(3)]
combined = combine(results)
# 型: Result[tuple[int, ...], E]
# 値: Ok((1, 2, 3))
```

### 2. すべてのエラーを収集：`combine_errors`

最初のエラーではなく、**すべてのエラー**を収集したい場合：

```python
from app.core.result import combine_errors

results = [Ok(1), Err("error1"), Ok(3), Err("error2")]
combined = combine_errors(results)
# -> Err(["error1", "error2"])
```

**いつcombine_errorsを使う？**
- ✅ フォームバリデーションで、すべてのエラーをユーザーに表示したい
- ✅ バッチ処理で、すべての失敗を記録したい
- ❌ 最初のエラーで十分な場合は`combine`を使う

### 3. 非同期処理：`ResultAwaitable`

`async/await`と`Result`を組み合わせる場合：

```python
from app.mediator import Mediator
from app.usecases.users.get_user import GetUserQuery

# メソッドチェーンしてから await
user_name = await (
    Mediator.send_async(GetUserQuery(user_id=1))
    .map(lambda user: user.name)
    .unwrap()
)
```

**なぜResultAwaitable？**
- `await`の前に`map`や`and_then`でメソッドチェーン可能
- Fluent APIにより、非同期処理が読みやすくなる
- 内部で適切に型が保持される

---

## ベストプラクティス

### ✅ すべき事

1. **Use Caseのレイヤーで使用**
   ```python
   # Use Case層
   def create_user(name: str) -> Result[User, UseCaseError]:
       # バリデーション、ビジネスロジック
       return Ok(user)
   ```

2. **match文で網羅的に処理**
   ```python
   match result:
       case Ok(value):
           # 成功時の処理
       case Err(error):
           # エラー時の処理
   ```

3. **mapとand_thenでチェーン**
   ```python
   result = (
       get_user(user_id)
       .map(lambda user: user.email)
       .and_then(validate_email)
   )
   ```

4. **型アノテーションを明示**
   ```python
   def process() -> Result[User, UseCaseError]:
       # 型を明示することで、呼び出し側が扱いやすい
   ```

### ❌ 避けるべき事

1. **unwrapの多用**
   ```python
   # 良くない - 例外に戻ってしまう
   user = get_user(user_id).unwrap()
   ```

2. **例外とResultの混在**
   ```python
   # 良くない - エラーハンドリングが統一されていない
   def process() -> Result[User, UseCaseError]:
       if error:
           raise ValueError()  # Errを返すべき
   ```

3. **深いネスト**
   ```python
   # 良くない
   match result1:
       case Ok(value1):
           match result2:
               case Ok(value2):
                   ...

   # 良い - combineやand_thenを使う
   combined = combine([result1, result2])
   ```

### 🎯 実践的なパターン

#### パターン1：早期リターン

```python
def process_order(order_id: int) -> Result[str, UseCaseError]:
    order_result = get_order(order_id)
    if is_err(order_result):
        return order_result
    order = order_result.value

    payment_result = process_payment(order)
    if is_err(payment_result):
        return payment_result

    return Ok("Order processed")
```

#### パターン2：タプルパターンマッチ（2つのResult）

```python
user_result = get_user(user_id)
item_result = get_item(item_id)

match (user_result, item_result):
    case (Ok(user), Ok(item)):
        return Ok(f"{user.name} bought {item.name}")
    case (Err(error), _) | (_, Err(error)):
        return Err(error)
```

#### パターン3：複数のResultを集約

```python
# 3つ以上の場合
results = [
    validate_name(name),
    validate_email(email),
    validate_age(age),
]

combined = combine(results)

match combined:
    case Ok([name, email, age]):
        return create_user(name, email, age)
    case Err(error):
        return Err(error)
```

---

## 関連ドキュメント

- [`app/core/result_usage_examples.md`](../../app/core/result_usage_examples.md) - より詳細な利用パターン
- `app/usecases/result.py` - UseCaseError型の定義
- Rust言語の[`Result`型ドキュメント](https://doc.rust-lang.org/std/result/)

---

## まとめ

**Result型の本質：**
- エラーを値として扱うことで、型システムで追跡可能にする
- Railway-oriented programmingによる安全なエラー伝播
- 関数型プログラミングの原則を取り入れた、実用的な設計

**いつ使うべきか：**
- ✅ Use Case層でのビジネスロジック
- ✅ 失敗しうる操作（バリデーション、外部API呼び出し、DB操作）
- ✅ エラーハンドリングを明示的にしたい場合

**いつ使わないべきか：**
- ❌ プログラムのバグ（`AssertionError`など）
- ❌ リカバリー不可能なエラー（メモリ不足など）
- ❌ 内部の実装詳細（例外で十分な場合）

Result型は、**型安全性**と**明示的なエラーハンドリング**を両立させる強力なツールです。適切に使用することで、より堅牢で保守性の高いコードを書くことができます。
