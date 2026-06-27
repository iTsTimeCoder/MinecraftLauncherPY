import os
import sys
import json
import subprocess
import time
import ctypes
import shutil
import minecraft_launcher_lib

if os.name == 'nt':
    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)

C_RESET = "\033[0m"
C_BOLD = "\033[1m"
C_CYAN = "\033[36m"
C_GREEN = "\033[32m"
C_YELLOW = "\033[33m"
C_RED = "\033[31m"
C_MAGENTA = "\033[35m"
C_WHITE = "\033[37m"

appdata_path = os.getenv('APPDATA')
minecraft_directory = os.path.join(appdata_path, ".mylauncher")
config_path = os.path.join(minecraft_directory, "launcher_config.json")
logs_directory = os.path.join(minecraft_directory, "logs")

os.makedirs(minecraft_directory, exist_ok=True)
os.makedirs(logs_directory, exist_ok=True)

def load_settings():
    # الإعداد الافتراضي للرام أصبح 2048 ميغابايت
    default_settings = {
        "username": "Player",
        "version": "1.16.5",
        "max_ram": 2048
    }
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return default_settings
    return default_settings

def save_settings(settings):
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=4)
    except:
        pass

def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')

def set_status(status: str):
    print(f"{C_YELLOW}[Status]{C_RESET} {status}")

def set_progress(progress: int):
    pass

def is_version_installed(version_id):
    version_jar = os.path.join(minecraft_directory, "versions", version_id, f"{version_id}.jar")
    return os.path.exists(version_jar)

def get_system_ram_suggestion():
    try:
        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong)
            ]
        stat = MEMORYSTATUSEX()
        stat.dwLength = ctypes.sizeof(stat)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
        total_gb = round(stat.ullTotalPhys / (1024 ** 3))
        
        # اقتراحات ذكية محسوبة بالميغابايت لتناسب الأجهزة الضعيفة والمتوسطة
        if total_gb <= 4:
            suggested_mb = 2048  # ترك مساحة كافية للويندوز 10/11 ليتحرك
        elif total_gb <= 8:
            suggested_mb = 4096
        elif total_gb <= 16:
            suggested_mb = 6144
        else:
            suggested_mb = 8192
        return total_gb, suggested_mb
    except:
        return 8, 4096

def find_java_executable():
    runtime_dir = os.path.join(minecraft_directory, "runtime")
    if os.path.exists(runtime_dir):
        for root, dirs, files in os.walk(runtime_dir):
            for file in files:
                if file == "javaw.exe":
                    return os.path.join(root, file)
        for root, dirs, files in os.walk(runtime_dir):
            for file in files:
                if file in ("java.exe", "java"):
                    return os.path.join(root, file)
    return "java"

def change_version(settings):
    clear_console()
    print(f"{C_CYAN}========================================{C_RESET}")
    print(f"{C_BOLD}{C_MAGENTA}          MINECRAFT VERSIONS            {C_RESET}")
    print(f"{C_CYAN}========================================{C_RESET}")
    print(f" {C_GREEN}Local Installed Versions:{C_RESET}")
    try:
        installed_versions = minecraft_launcher_lib.utils.get_installed_versions(minecraft_directory)
        if installed_versions:
            for v in installed_versions:
                print(f"  {C_WHITE}- {v['id']}{C_RESET}")
        else:
            print(f"  {C_RED}No local versions found.{C_RESET}")
    except:
        print(f"  {C_RED}Could not read local versions.{C_RESET}")
    print(f"{C_CYAN}========================================{C_RESET}")
    new_ver = input(f" {C_GREEN}Enter Version ID (e.g., 1.16.5, 1.20.1):{C_RESET} ").strip()
    if new_ver:
        settings["version"] = new_ver
        save_settings(settings)

def change_ram(settings):
    clear_console()
    total_pc_ram, dynamic_suggestion = get_system_ram_suggestion()
    print(f"{C_CYAN}========================================{C_RESET}")
    print(f"{C_BOLD}{C_MAGENTA}           RAM ALLOCATION               {C_RESET}")
    print(f"{C_CYAN}========================================{C_RESET}")
    print(f" {C_WHITE}Your System Total RAM:{C_RESET} {C_GREEN}{total_pc_ram} GB{C_RESET}")
    print(f" {C_WHITE}AI Optimized Suggestion:{C_RESET} {C_CYAN}{dynamic_suggestion} MB{C_RESET}")
    print(f"{C_CYAN}========================================{C_RESET}")
    print(f" {C_YELLOW}Examples: 2048 MB (2GB) | 3072 MB (3GB) | 4096 MB (4GB){C_RESET}")
    print(f"{C_CYAN}----------------------------------------{C_RESET}")
    
    new_ram = input(f" {C_GREEN}Enter Max RAM size in MB [Leave empty for suggestion]:{C_RESET} ").strip()
    
    if new_ram.isdigit():
        ram_val = int(new_ram)
        
        # حماية ذكية: لو المستخدم كتب مثلاً "2" أو "3" بالخطأ، نقوم بتحويلها تلقائياً إلى ميغابايت
        if ram_val < 32:
            print(f"\n{C_YELLOW}[!] Detected GB notation. Automatically converting {ram_val}GB to {ram_val * 1024}MB...{C_RESET}")
            ram_val = ram_val * 1024
            time.sleep(1.5)
            
        # تحذير في حال تعدي حدود الأمان لرام الجهاز
        if ram_val >= (total_pc_ram * 1024):
            print(f"\n{C_RED}[Warning] You are allocating ALL or MORE than your system RAM. Windows might crash!{C_RESET}")
            confirm = input(" Are you sure you want to keep this setting? (y/n): ").strip().lower()
            if confirm != 'y':
                return

        settings["max_ram"] = ram_val
        save_settings(settings)
    elif not new_ram:
        settings["max_ram"] = dynamic_suggestion
        save_settings(settings)

def install_local_jar():
    clear_console()
    print(f"{C_CYAN}========================================{C_RESET}")
    print(f"{C_BOLD}{C_MAGENTA}        MANUAL MODLOADER/JAR FILE       {C_RESET}")
    print(f"{C_CYAN}========================================{C_RESET}")
    print(f" {C_WHITE}Official Download Links:{C_RESET}")
    print(f" - OptiFine: {C_YELLOW}https://optifine.net/downloads{C_RESET}")
    print(f" - Forge:    {C_YELLOW}https://files.minecraftforge.net{C_RESET}")
    print(f"{C_CYAN}----------------------------------------{C_RESET}")
    
    print(f"\n{C_CYAN}Scanning for .jar files next to the launcher script...{C_RESET}")
    jar_files = [f for f in os.listdir('.') if f.endswith('.jar')]
    
    if not jar_files:
        print(f"{C_RED}No .jar files found! Please drop your OptiFine/Forge .jar file right next to this python script and try again.{C_RESET}")
        input("\nPress Enter to return...")
        return
    
    print(f"\n{C_GREEN}Found the following files:{C_RESET}")
    for idx, jar in enumerate(jar_files):
        print(f" [{idx + 1}] {jar}")
        
    f_choice = input(f"\nSelect the file to install (1-{len(jar_files)}): ").strip()
    if not f_choice.isdigit() or int(f_choice) < 1 or int(f_choice) > len(jar_files):
        print(f"{C_RED}Invalid Selection.{C_RESET}")
        input("\nPress Enter to return...")
        return
        
    selected_jar = jar_files[int(f_choice) - 1]
    
    print(f"\n{C_WHITE}Selected File:{C_RESET} {C_YELLOW}{selected_jar}{C_RESET}")
    custom_name = input(f" {C_GREEN}Enter Custom Profile Name (Leave empty for default name):{C_RESET} ").strip()
    
    versions_dir = os.path.join(minecraft_directory, "versions")
    os.makedirs(versions_dir, exist_ok=True)
    old_versions = set(os.listdir(versions_dir))
    
    print(f"\n{C_CYAN}Starting official installer process...{C_RESET}")
    try:
        java_executable = find_java_executable()
        
        if java_executable == "java":
            try:
                subprocess.run(["java", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except FileNotFoundError:
                print(f"\n{C_RED}Error: Java could not be detected on your PC!{C_RESET}")
                print(f"{C_YELLOW}Please launch a Vanilla version from the main menu at least once first.{C_RESET}")
                print(f"{C_YELLOW}This will force the launcher to download the proper internal Java runtime files automatically.{C_RESET}")
                input("\nPress Enter to continue...")
                return

        if "optifine" in selected_jar.lower():
            print(f"{C_YELLOW}Opening OptiFine GUI window. The launcher path has been filled automatically. Just click 'Install'.{C_RESET}")
            subprocess.run([java_executable, "-jar", selected_jar, minecraft_directory])
        else:
            print(f"{C_YELLOW}Installing Forge client silently... Please wait.{C_RESET}")
            subprocess.run([java_executable, "-jar", selected_jar, "--installClient", minecraft_directory])
            
        new_versions = set(os.listdir(versions_dir))
        added_versions = new_versions - old_versions
        
        if added_versions:
            detected_version = list(added_versions)[0]
            if custom_name:
                old_folder_path = os.path.join(versions_dir, detected_version)
                new_folder_path = os.path.join(versions_dir, custom_name)
                
                if os.path.exists(new_folder_path):
                    shutil.rmtree(new_folder_path)
                os.rename(old_folder_path, new_folder_path)
                
                old_json_path = os.path.join(new_folder_path, f"{detected_version}.json")
                new_json_path = os.path.join(new_folder_path, f"{custom_name}.json")
                if os.path.exists(old_json_path):
                    os.rename(old_json_path, new_json_path)
                    with open(new_json_path, "r", encoding="utf-8") as f:
                        json_data = json.load(f)
                    json_data["id"] = custom_name
                    with open(new_json_path, "w", encoding="utf-8") as f:
                        json.dump(json_data, f, indent=4)
                print(f"\n{C_GREEN}Successfully installed and renamed to profile: {custom_name}{C_RESET}")
            else:
                print(f"\n{C_GREEN}Successfully installed profile: {detected_version}{C_RESET}")
        else:
            print(f"\n{C_RED}Installation completed, but no profile folder was generated. Ensure you clicked 'Install' or the jar file is correct.{C_RESET}")
    except Exception as e:
        print(f"\n{C_RED}An error occurred during installation: {e}{C_RESET}")
    input("\nPress Enter to continue...")

def install_modloaders(settings):
    while True:
        clear_console()
        print(f"{C_CYAN}========================================{C_RESET}")
        print(f"{C_BOLD}{C_MAGENTA}         MOD LOADERS INSTALLER          {C_RESET}")
        print(f"{C_CYAN}========================================{C_RESET}")
        print(f" Target Version: {C_GREEN}{settings['version']}{C_RESET}")
        print(f"{C_CYAN}----------------------------------------{C_RESET}")
        print(f" {C_WHITE}[1]{C_RESET} Install {C_CYAN}Fabric{C_RESET} (Automatic)")
        print(f" {C_WHITE}[2]{C_RESET} Install {C_CYAN}Forge{C_RESET} (Automatic)")
        print(f" {C_WHITE}[3]{C_RESET} Install {C_CYAN}Local Jar / OptiFine{C_RESET} (Manual)")
        print(f" {C_WHITE}[4]{C_RESET} Back to Main Menu{C_RESET}")
        print(f"{C_CYAN}========================================{C_RESET}")
        
        choice = input(f" {C_GREEN}Select an option (1-4):{C_RESET} ").strip()
        
        if choice == "1":
            clear_console()
            print(f"{C_CYAN}Step 1/2:{C_RESET} Verifying base vanilla files for {settings['version']}...")
            try:
                if not is_version_installed(settings["version"]):
                    minecraft_launcher_lib.install.install_minecraft_version(settings["version"], minecraft_directory)
                
                print(f"\n{C_CYAN}Step 2/2:{C_RESET} Fetching and installing latest Fabric loader...")
                minecraft_launcher_lib.fabric.install_fabric(settings["version"], minecraft_directory, callback={"setStatus": set_status, "setProgress": set_progress})
                
                print(f"\n{C_GREEN}Fabric successfully installed!{C_RESET}")
                print("Go to 'Select Version' in main menu to switch to the Fabric profile.")
            except Exception as e:
                print(f"\n{C_RED}Fabric installation failed: {e}{C_RESET}")
            input("\nPress Enter to continue...")
            
        elif choice == "2":
            clear_console()
            print(f"{C_CYAN}Step 1/2:{C_RESET} Verifying base vanilla files for {settings['version']}...")
            try:
                if not is_version_installed(settings["version"]):
                    minecraft_launcher_lib.install.install_minecraft_version(settings["version"], minecraft_directory)
                
                print(f"\n{C_CYAN}Step 2/2:{C_RESET} Searching available Forge versions for {settings['version']}...")
                forge_version = minecraft_launcher_lib.forge.find_forge_version(settings["version"])
                if forge_version:
                    print(f"Found Forge ID: {C_YELLOW}{forge_version}{C_RESET}. Downloading installer components...")
                    minecraft_launcher_lib.forge.install_forge_version(forge_version, minecraft_directory, callback={"setStatus": set_status, "setProgress": set_progress})
                    print(f"\n{C_GREEN}Forge successfully installed!{C_RESET}")
                    print("Go to 'Select Version' in main menu to switch to the Forge profile.")
                else:
                    print(f"\n{C_RED}No official Forge release found for version {settings['version']}.{C_RESET}")
            except Exception as e:
                print(f"\n{C_RED}Forge installation failed: {e}{C_RESET}")
            input("\nPress Enter to continue...")
            
        elif choice == "3":
            install_local_jar()
            
        elif choice == "4":
            break

def show_error_dialog(title, message):
    ctypes.windll.user32.MessageBoxW(0, message, title, 0x10 | 0x0)

def main():
    settings = load_settings()

    while True:
        clear_console()
        print(f"{C_CYAN}========================================{C_RESET}")
        print(f"{C_BOLD}{C_MAGENTA}          LAUNCHER CONFIGURATION        {C_RESET}")
        print(f"{C_CYAN}========================================{C_RESET}")
        print(f" {C_WHITE}[1]{C_RESET} {C_GREEN}Launch Minecraft{C_RESET}  ({settings['version']})")
        print(f" {C_WHITE}[2]{C_RESET} Edit Username     (Current: {C_YELLOW}{settings['username']}{C_RESET})")
        print(f" {C_WHITE}[3]{C_RESET} Select Version    (Current: {C_YELLOW}{settings['version']}{C_RESET})")
        print(f" {C_WHITE}[4]{C_RESET} Allocate RAM      (Current: {C_YELLOW}{settings['max_ram']} MB{C_RESET})")
        print(f" {C_WHITE}[5]{C_RESET} Install Mod Loader(Forge/Fabric/OptiFine)")
        print(f" {C_WHITE}[6]{C_RESET} {C_RED}Exit{C_RESET}")
        print(f"{C_CYAN}========================================{C_RESET}")
        
        choice = input(f" {C_GREEN}Select an option (1-6):{C_RESET} ").strip()

        if choice == "1":
            clear_console()
            
            try:
                if not is_version_installed(settings["version"]):
                    print(f"{C_YELLOW}Files missing or first time launch. Downloading game files...{C_RESET}")
                    minecraft_launcher_lib.install.install_minecraft_version(
                        version=settings["version"],
                        minecraft_directory=minecraft_directory,
                        callback={"setStatus": set_status, "setProgress": set_progress}
                    )
                else:
                    print(f"{C_GREEN}Game files verified successfully. Preparing to launch...{C_RESET}")
                
                # استخدام حزمة حرف M للإشارة للميغابايت، وتخفيض الحد الأدنى لبدء التشغيل لـ 512M لتوفير الموارد
                options = {
                    "username": settings["username"],
                    "uuid": "",
                    "token": "",
                    "jvmArguments": [f"-Xmx{settings['max_ram']}M", "-Xms512M"],
                    "executablePath": find_java_executable()
                }
                
                launch_command = minecraft_launcher_lib.command.get_minecraft_command(
                    version=settings["version"],
                    minecraft_directory=minecraft_directory,
                    options=options
                )
                
                log_path = os.path.join(logs_directory, "game_output.log")
                log_file = open(log_path, "w", encoding="utf-8")
                
                print(f"\n{C_CYAN}Launching Minecraft... Hiding CMD window.{C_RESET}")
                
                if os.name == 'nt':
                    hwnd = ctypes.windll.kernel32.GetConsoleWindow()
                    if hwnd:
                        ctypes.windll.user32.ShowWindow(hwnd, 0)
                
                process = subprocess.Popen(
                    launch_command, 
                    stdout=log_file, 
                    stderr=log_file,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )
                
                time.sleep(3)
                
                if process.poll() is not None:
                    log_file.close()
                    error_msg = "Minecraft crashed instantly on startup!"
                    try:
                        with open(log_path, "r", encoding="utf-8") as f:
                            errors = f.read()
                            if errors:
                                error_msg += f"\n\nDetails:\n{errors[:500]}"
                    except:
                        pass
                    
                    if os.name == 'nt' and hwnd:
                        ctypes.windll.user32.ShowWindow(hwnd, 5)
                    
                    show_error_dialog("Launch Error", error_msg)
                else:
                    sys.exit(0)
                    
            except Exception as e:
                if os.name == 'nt' and hwnd:
                    ctypes.windll.user32.ShowWindow(hwnd, 5)
                print(f"\n{C_RED}An error occurred: {e}{C_RESET}")
                input("\nPress Enter to return to menu...")

        elif choice == "2":
            clear_console()
            new_user = input(f" {C_GREEN}Enter new username:{C_RESET} ").strip()
            if new_user:
                settings["username"] = new_user
                save_settings(settings)

        elif choice == "3":
            change_version(settings)

        elif choice == "4":
            change_ram(settings)
            
        elif choice == "5":
            install_modloaders(settings)

        elif choice == "6":
            sys.exit(0)

if __name__ == "__main__":
    main()