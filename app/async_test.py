import asyncio


# 通常の関数(同期関数)
async def main():
    result = async_main()
    try:
        value = await result  # コルーチンを実行するためにawaitを使用
    except ValueError as e:
        print(f"ValueError: {e}")  # ValueErrorをキャッチして処理する


# コルーチン関数(非同期関数)
async def async_main() -> int:
    print("hello async world")
    await asyncio.sleep(1)
    raise ValueError("error")  # ValueErrorを発生させる


if __name__ == "__main__":
    asyncio.run(main())  # asyncio.run()を使用して非同期関数を実行する
