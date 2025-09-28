import asyncio
from pathlib import Path

from pure_ai_generator import PureAIGenerator


async def main() -> None:
    generator = PureAIGenerator()
    try:
        files = await generator.generate_project_structure(
            Path("generated_projects/debug-app"),
            "Debug a collaborative task board with analytics",
            "debug-app",
        )
    except Exception as exc:  # noqa: BLE001 - surfacing raw exception for debug
        print("ERROR", type(exc).__name__, exc)
    else:
        print("SUCCESS", len(files))
        for path in files:
            print(" -", path)


if __name__ == "__main__":
    asyncio.run(main())
