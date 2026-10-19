import sys
import argparse
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from app.services.seed_service import seed_service

def main():
    parser = argparse.ArgumentParser(description="Заполнение БД тестовыми данными (1000 записей).")
    parser.add_argument("--count", type=int, default=1000, help="Количество записей (по умолчанию 1000)")
    parser.add_argument("--db", type=str, default="all", help="Целевая БД: all, postgres, sqlite, mysql, mongodb, mssql, oracle")
    args = parser.parse_args()

    print(f"=== Запуск генерации и загрузки данных ({args.count} записей) ===")
    if args.db.lower() == "all":
        result = seed_service.seed_all(count=args.count)
        print(f"\nВсего сгенерировано записей: {result['total_users']}")
        print("-" * 50)
        for db_name, res in result["results"].items():
            if res["success"]:
                print(f"[OK] {res['display_name']}: добавлено {res['count']} строк за {res['duration_ms']} мс")
            else:
                print(f"[FAIL] {res['display_name']}: ошибка -> {res.get('error')}")
    else:
        res = seed_service.seed_single_db(args.db.lower(), count=args.count)
        if res["success"]:
            print(f"[OK] {res['display_name']}: добавлено {res['count']} строк за {res['duration_ms']} мс")
        else:
            print(f"[FAIL] {res.get('display_name', args.db)}: ошибка -> {res.get('error')}")

    print("\nГотово!")

if __name__ == "__main__":
    main()
