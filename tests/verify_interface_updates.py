import sys
from pathlib import Path

def check_file_content(path, strings_to_find):
    try:
        content = Path(path).read_text(encoding='utf-8')
        missing = [s for s in strings_to_find if s not in content]
        if missing:
            print(f"[FAIL] {path}: Missing {missing}")
            return False
        print(f"[OK] {path}: Verified")
        return True
    except Exception as e:
        print(f"[ERR] {path}: Error {e}")
        return False

def verify_interfaces():
    print("Verifying Interface Updates (Phase 20-23)...")
    
    # 1. Web Interface
    web_ok = check_file_content("d:/Projects/siya/web/static/index.html", [
        'id="mode-select"',
        'id="posture-widget"',
        'value="informational"',
        'value="destructive"'
    ])
    
    js_ok = check_file_content("d:/Projects/siya/web/static/app.js", [
        'function loadIntentMode',
        'function setIntentMode',
        'function loadPosture',
        'function explainAction',
        'get_user_intent_mode', 
        'get_system_posture'
    ])

    # 2. CLI
    cli_ok = check_file_content("d:/Projects/siya/pc_mcp_client/main.py", [
        'sub.add_parser("explain"',
        'sub.add_parser("mode"', 
        'sub.add_parser("posture"',
        'explain_decision',
        'get_system_posture'
    ])

    # 3. TUI
    tui_ok = check_file_content("d:/Projects/siya/pc_mcp_client/tui/app.py", [
        'id="mode-status"',
        'id="posture-status"',
        'def update_status(self)',
        'get_user_intent_mode',
        'get_system_posture'
    ])

    if all([web_ok, js_ok, cli_ok, tui_ok]):
        print("\n[SUCCESS] Verification Successful: All interfaces verified.")
        sys.exit(0)
    else:
        print("\n[FAILURE] Verification Failed")
        sys.exit(1)

if __name__ == "__main__":
    verify_interfaces()
