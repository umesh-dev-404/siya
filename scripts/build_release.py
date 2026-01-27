
import os
import shutil
import subprocess
import sys
from glob import glob

def main():
    print("🚀 Starting Siya Release Build...")
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(root_dir)

    # 1. Clean dist/ directory
    dist_dir = os.path.join(root_dir, "dist")
    if os.path.exists(dist_dir):
        print("🧹 Cleaning old artifacts...")
        shutil.rmtree(dist_dir)
    
    # 2. Verify build dependency
    try:
        import build
    except ImportError:
        print("❌ 'build' package not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "build"])

    # 3. Build package
    print("📦 Building package (sdist + wheel)...")
    try:
        subprocess.check_call([sys.executable, "-m", "build"])
    except subprocess.CalledProcessError:
        print("❌ Build failed!")
        sys.exit(1)

    # 4. Report results
    print("\n✅ Build Complete!")
    print("📂 Artifacts in 'dist/':")
    
    wheels = glob(os.path.join(dist_dir, "*.whl"))
    for f in wheels:
        print(f"  - {os.path.basename(f)}")

    if not wheels:
        print("⚠️ No wheels found? Something went wrong.")
        sys.exit(1)

    latest_wheel = wheels[0]
    print(f"\n👉 To install on a new machine, copy '{os.path.basename(latest_wheel)}' and run:")
    print(f"   pip install {os.path.basename(latest_wheel)}")

if __name__ == "__main__":
    main()
