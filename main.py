"""Lineage Classic 游戏辅助工具 — 统一启动器

用法:
    python main.py                    交互式菜单
    python main.py single-mage        单端法师
    python main.py dual-mage          双端法师
    python main.py attacker           打手发送端
    python main.py party-mage         团队法师（站桩奶妈）
    python main.py attacker -v        打手端（DEBUG 详细日志）
"""

import argparse
import sys
import traceback

from src.config import LOG_LEVEL, validate_config
from src.utils.logger import get_logger, set_log_level


ROLES = {
    "single-mage": ("单端法师", "src.roles.single_mage", "SingleMageRole"),
    "dual-mage":   ("双端法师", "src.roles.dual_mage",   "DualMageRole"),
    "attacker":    ("打手发送端", "src.roles.attacker",   "AttackerRole"),
    "party-mage":  ("团队法师", "src.roles.party_mage",  "StationaryHealerRole"),
}


def show_menu() -> str:
    print("=" * 40)
    print("  Lineage Classic 辅助工具")
    print("=" * 40)
    for i, (key, (name, _, _)) in enumerate(ROLES.items(), 1):
        print(f"  {i}. {name} ({key})")
    print("  q. 退出")
    print("-" * 40)

    while True:
        choice = input("请选择 > ").strip().lower()
        if choice == 'q':
            sys.exit(0)
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(ROLES):
                return list(ROLES.keys())[idx]
        for key in ROLES:
            if choice == key:
                return key
        print("无效选择，请重试")


def run_role(role_key: str) -> None:
    _, module_path, class_name = ROLES[role_key]
    mod = __import__(module_path, fromlist=[class_name])
    role_class = getattr(mod, class_name)
    role = role_class()
    role.run()


def main() -> None:
    parser = argparse.ArgumentParser(description="Lineage Classic 辅助工具")
    parser.add_argument(
        "role", nargs="?", choices=list(ROLES.keys()),

        help="角色类型（不填则显示菜单）"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="详细日志（DEBUG 级别）"
    )
    args = parser.parse_args()

    if args.verbose:
        set_log_level("DEBUG")
    else:
        set_log_level(LOG_LEVEL)

    try:
        validate_config()
    except ValueError as e:
        print(f"配置错误: {e}")
        sys.exit(1)

    role_key = args.role if args.role else show_menu()
    name = ROLES[role_key][0]
    print(f"\n启动 {name}...\n")

    try:
        run_role(role_key)
    except Exception:
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
