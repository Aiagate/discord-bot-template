`DomainEntityBase` を使用した「外部からは不変、内部（ドメインロジック）からは変更可能」な実装手順をまとめます。

この設計により、**「初期化(`__init__`)はクリーンに保ちつつ、堅牢なカプセル化を実現」** できます。

### ディレクトリ構成イメージ

```text
src/
 ├── domain/
 │   ├── shared/
 │   │   └── base.py       # DomainEntityBase (基底クラス)
 │   └── model/
 │       └── player.py     # Player (具体的なエンティティ)
 ├── main.py               # 動作確認用
 └── pyproject.toml        # Pyright設定 (または pyrightconfig.json)
```

-----

### 手順 1: 基底クラスの作成 (`DomainEntityBase`)

ドメイン層の共通部品として定義します。このクラスは「自身の値を強制的に書き換える権限」をサブクラスに提供します。

**ファイル:** `src/domain/shared/base.py`

```python
from typing import Any

class DomainEntityBase:
    """
    ドメインエンティティの基底クラス。
    frozen=True なデータクラスに対し、ドメインメソッド経由でのみ
    内部状態を変更する機能を提供します。
    """
    def _update_state(self, field_name: str, value: Any) -> None:
        """
        [Protected] 内部状態を更新します。
        このメソッドは、ドメインモデルのメソッド内でのみ呼び出してください。
        """
        # frozen=True の制限を回避して値をセットする
        object.__setattr__(self, field_name, value)
```

-----

### 手順 2: エンティティの実装 (`Player`)

基底クラスを継承し、`frozen=True` を付与します。
**ポイントは、フィールド名に `_` を付けないことです。**

**ファイル:** `src/domain/model/player.py`

```python
from dataclasses import dataclass
from src.domain.shared.base import DomainEntityBase

@dataclass(frozen=True) # これにより、外部からの代入(player.hp = 0)は禁止される
class Player(DomainEntityBase):
    # フィールドは公開名で定義する（これにより __init__ の引数も 'hp' になる）
    name: str
    hp: int
    max_hp: int

    def take_damage(self, amount: int) -> None:
        """
        ダメージを受ける（ドメインロジック）。
        状態変更は必ずこのメソッドのような「振る舞い」を通じて行う。
        """
        new_hp = max(0, self.hp - amount)

        # 親クラスの _update_state を使って自身の 'hp' フィールドを更新
        self._update_state("hp", new_hp)
        print(f"{self.name} took {amount} damage! HP: {self.hp}")

    def heal(self, amount: int) -> None:
        """回復ロジック"""
        new_hp = min(self.max_hp, self.hp + amount)
        self._update_state("hp", new_hp)
        print(f"{self.name} healed {amount}! HP: {self.hp}")
```

-----

### 手順 3: Pyrightの設定（ルールの強制）

「メソッドを経由せずに `_update_state` を呼ぶ」といった不正行為をエディタ上でエラーにするため、設定を追加します。

**ファイル:** `pyproject.toml` (または `pyrightconfig.json`)

```toml
[tool.pyright]
reportPrivateUsage = "error"
```

これにより、外部から `player._update_state(...)` を呼ぼうとすると静的解析エラーになります。

-----

### 手順 4: 利用と動作確認

実装したクラスを使用します。初期化が非常に自然であることがわかります。

**ファイル:** `src/main.py`

```python
from src.domain.model.player import Player
from dataclasses import FrozenInstanceError

def main():
    # 1. 初期化
    # アンダースコアなしの綺麗な引数名でインスタンス化できる
    hero = Player(name="Aragorn", hp=100, max_hp=100)

    print(f"Start: {hero}")

    # 2. 正当な変更（ドメインメソッド経由）
    # 内部で _update_state が呼ばれ、値が更新される
    hero.take_damage(30)

    # 3. 不正な変更の防止（直接代入）
    try:
        hero.hp = 9999
    except FrozenInstanceError:
        print("Block: 直接代入は frozen=True により実行時エラーになります。")

    # 4. 不正な変更の防止（Protectedメソッドへのアクセス）
    # 実行はできてしまうが、Pyrightがここで「reportPrivateUsage」エラーを出す
    # エディタ上で赤い波線が表示される
    # hero._update_state("hp", 0)

if __name__ == "__main__":
    main()
```

### まとめ：この実装で達成できたこと

1. **初期化が綺麗:** `Player(hp=100)` と自然に書ける（`_hp=100` と書かなくて良い）。
2. **外部からは読み取り専用:** `player.hp` は参照できるが、`player.hp = 0` はエラーになる。
3. **内部からは変更可能:** `take_damage` メソッド内でのみ値を更新できる。
4. **ルール違反を検知:** ドメイン層以外で裏技的に値を書き換えようとすると、Pyrightが警告を出す。
