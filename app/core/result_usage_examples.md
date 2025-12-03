# Result型 利用パターンガイド

このドキュメントでは、`app.core.result`で定義されている`Result`型（`Ok` | `Err`）の基本的な使い方と、複数の`Result`を扱う際のベストプラクティスについて解説します。

## 1. 基本的な使い方 (`match`文)

`Result`型を返す関数を扱う最も基本的な方法は、`match`文を使うことです。これにより、成功 (`Ok`) と失敗 (`Err`) の両方のケースを網羅的に処理できます。

```python
from app.core.result import Result, Ok, Err, combine

def find_user(user_id: int) -> Result[str, str]:
    if user_id == 1:
        return Ok("Alice")
    else:
        return Err("User not found")

# --- 使用例 ---
result = find_user(1)

match result:
    case Ok(user_name):
        print(f"Success: Welcome, {user_name}!")
        # -> Success: Welcome, Alice!
    case Err(error_message):
        print(f"Error: {error_message}")
```

`case Ok(user_name):` のように書くことで、`Ok`インスタンスから値を変数 `user_name` に直接取り出すことができる（構造的パターンマッチング）のが大きな利点です。

## 2. 複数の`Result`を扱う場合

複数の`Result`を返す処理を組み合わせる際には、ネストが深くなりすぎないように注意が必要です。

### アンチパターン：`match`のネスト

単純に`match`をネストさせると、インデントが深くなり、コードが非常に読みにくくなります（"Pyramid of Doom"）。

```python
# --- 良くない例 ---
# def find_item() -> Result...
user_result = find_user(1)
item_result = find_item("sword")

match user_result:
    case Ok(user):
        match item_result:
            case Ok(item):
                print(f"{user} found a {item}.")
            # ...
```

### パターンA：早期リターン（Guard Clause）

各処理の後にエラーチェックを行い、`Err`であればその場で処理を中断してリターンする方法です。コードがフラットになり、手続き的なロジックで理解しやすくなります。

```python
def process_user_and_item():
    user_result = find_user(1)
    if isinstance(user_result, Err):
        return user_result
    user = user_result.value

    item_result = find_item("sword")
    if isinstance(item_result, Err):
        return item_result
    item = item_result.value

    return Ok(f"{user} has a {item}")
```

### パターンB：タプルを使ったパターンマッチ（2つの場合に最適）

Python 3.10の`match`文はタプルも扱えます。複数の`Result`をタプルにまとめて一度にマッチさせることで、ネストを避けつつ、すべての成功・失敗の組み合わせをエレガントに記述できます。**これは特に2つの`Result`を扱う場合に非常に有効です。**

```python
user_result = find_user(1)
item_result = find_item("sword")

match (user_result, item_result):
    case (Ok(user), Ok(item)):
        print(f"{user} is equipped with a {item}.")
    case (Err(user_error), _):
        print(f"User error: {user_error}")
    case (_, Err(item_error)):
        print(f"Item error: {item_error}")
```

### パターンC：ループによる逐次チェック（`combine`関数の内部実装）

タプルマッチは`Result`の数が3つ以上になると`case`文の組み合わせが複雑になります。この問題を解決する**`combine`関数は、内部でforループと早期リターンを組み合わせることで、多数の`Result`をフラットかつスケーラブルに扱っています。** 以下のコードは、`combine`関数がどのように動作しているかを示すものです。**通常、このロジックを直接記述する必要はなく、`combine`関数を利用することを推奨します。**

```python
def get_system_status() -> Result[str, str]:
    return Ok("Ready")

def process_many_results_manual():
    results = [ find_user(1), find_item("sword"), get_system_status() ]
    ok_values = []
    for res in results:
        match res:
            case Ok(value):
                ok_values.append(value)
            case Err(error):
                return Err(error) # 最初のエラーでリターン

    # ... 全て成功した場合の処理 ...
    return Ok(tuple(ok_values))
```

### パターンD：`combine`ヘルパー関数による集約（推奨）

パターンCのロジックを再利用可能な関数としてカプセル化したのが`combine`関数です。これにより、利用者はループ処理を意識することなく、宣言的に複数の`Result`を扱えます。

**これが、3つ以上の`Result`を扱う上で最も推奨されるパターンです。**

```python
def process_with_combine():
    results = [
        find_user(1),
        find_item("sword"),
        get_system_status(),
    ]

    # 複数のResultを一つのResultに集約
    combined_result = combine(results)

    # あとは通常通り、単一のResultとして扱える
    match combined_result:
        case Ok(values):
            # 全て成功した場合。valuesは (str, str, str) のタプル
            user, item, status = values
            print(f"Success! User: {user}, Item: {item}, Status: {status}")
            return Ok(values)
        case Err(error):
            # 最初に発生したエラー
            print(f"An error occurred: {error}")
            return Err(error)

process_with_combine()
```

この方法は、コードの意図が明確になり、`Result`の数が増えてもコードの複雑さが変わらないという大きなメリットがあります。

---

## 結論

以上のパターンを参考に、状況に応じて最適な方法を選択してください。

- **1つ**の`Result`には、基本的な**`match`文**。
- **2つ**の`Result`には、**タプルでのパターンマッチ**が簡潔で有効。
- **3つ以上**の`Result`には、**`combine`関数**を利用するのが最もクリーンでスケールする解決策です。
  パターンCの「ループによる逐次チェック」は`combine`関数の内部実装を理解するためのものであり、直接コードに記述することは**非推奨**です。

---

## 3. 異なる型のResultを組み合わせる（ヘテロジニアス型）

`combine`関数は、異なる型の`Result`を扱うこともできます。この場合、**タプル**で渡すことで、各要素の型が保持されます。

### 基本的な使い方

```python
from app.core.result import Result, Ok, Err, combine
from app.usecases.result import UseCaseError, ErrorType

def validate_user_creation(
    name: str,
    age: int
) -> Result[tuple[str, int], UseCaseError]:
    """ユーザー作成時のバリデーション"""
    # 各フィールドを個別に検証
    name_result: Result[str, UseCaseError] = validate_name(name)
    age_result: Result[int, UseCaseError] = validate_age(age)

    # タプルで渡すと、異なる型(str, int)を一つにまとめられる
    combined = combine((name_result, age_result))

    match combined:
        case Ok((valid_name, valid_age)):
            # valid_nameはstr型、valid_ageはint型として推論される
            return Ok((valid_name, valid_age))
        case Err(error):
            return Err(error)
```

### メリット

1. **型安全性**: 各要素の型が正しく推論される（`any`にならない）
2. **スケーラビリティ**: 最大10個までの異なる型を組み合わせ可能
3. **コンパイル時チェック**: Pyrightが型の不一致を検出

### 実例：複数フィールドのバリデーション

```python
def create_user_account(
    user_id: str,
    email: str,
    age: str,
    is_premium: str,
) -> Result[UserAccount, UseCaseError]:
    # 各フィールドをバリデーション（型変換含む）
    uid_result: Result[int, UseCaseError] = parse_user_id(user_id)
    email_result: Result[str, UseCaseError] = validate_email(email)
    age_result: Result[int, UseCaseError] = parse_age(age)
    premium_result: Result[bool, UseCaseError] = parse_bool(is_premium)

    # 4つの異なる型を組み合わせる
    combined = combine((uid_result, email_result, age_result, premium_result))
    # 型: Result[tuple[int, str, int, bool], UseCaseError]

    match combined:
        case Ok((uid, mail, user_age, is_premium)):
            # uid: int, mail: str, user_age: int, is_premium: bool
            return Ok(UserAccount(uid, mail, user_age, is_premium))
        case Err(error):
            return Err(error)  # 最初のエラーを返す
```

### 同じ型の場合はリストも使える

```python
# 同じ型の場合はリストでもOK（後方互換性）
results = [Ok(1), Ok(2), Ok(3)]
combined = combine(results)
# 型: Result[tuple[int, ...], E]
# 値: Ok((1, 2, 3))
```

### タプル vs リスト

| 用途 | 使用方法 | 型推論 |
|------|---------|--------|
| **異なる型** | タプル `combine((res1, res2))` | `Result[tuple[T1, T2], E]` |
| **同じ型** | リストまたはタプル `combine([res1, res2])` | `Result[tuple[T, ...], E]` |

### 注意点

- **戻り値はタプル**: `combine`は常にタプル（`tuple`）を返します（以前は`list`でしたが変更されました）
- **最初のエラーを返す**: 複数のエラーがある場合、最初に見つかったエラーが返されます
- **エラー型は統一**: すべての`Result`のエラー型`E`は同じである必要があります
