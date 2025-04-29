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
