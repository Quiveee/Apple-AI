import os
import sys
import json
import shutil
import time

try:
    from colorama import init, Fore, Style
    init()
    COLORAMA_AVAILABLE = True
except ImportError:
    print("Note: colorama not installed. Install with: pip install colorama")
    COLORAMA_AVAILABLE = False

# ============================================================================
# FILTER CRITERIA CLASS - Stores all filter settings
# ============================================================================

class FilterCriteria:
    
    def __init__(self):
        self.only_files = False
        self.only_dirs = False
        self.only_jar = False
        self.only_json = False
        self.size_less_than_1mb = False
        self.size_more_than_1mb = False
        self.exclude_keyword = None
        self.include_keyword = None
        self.modified_last_24h = False
        self.modified_over_24h = False
        self.show_tree = False
        
    def should_include(self, entry_name, entry_path, is_dir):
        
        # Filter 1: Only files
        if self.only_files and is_dir:
            return False
        
        # Filter 2: Only directories
        if self.only_dirs and not is_dir:
            return False
        
        # If it's a directory, skip remaining file-specific filters
        if is_dir:
            return True
        
        # Filter 3: Only JAR files
        if self.only_jar and not entry_name.lower().endswith(".jar"):
            return False
        
        # Filter 4: Only JSON files
        if self.only_json and not entry_name.lower().endswith(".json"):
            return False
        
        # Filter 5 & 6: Size filters (need to check file size)
        try:
            file_size_kb = os.path.getsize(entry_path) / 1024
            
            if self.size_less_than_1mb and file_size_kb >= 1024:
                return False
            
            if self.size_more_than_1mb and file_size_kb < 1024:
                return False
        except:
            pass  # If we can't get size, skip size filters
        
        # Filter 7: Exclude keyword
        if self.exclude_keyword and self.exclude_keyword.lower() in entry_name.lower():
            return False
        
        # Filter 8: Include keyword
        if self.include_keyword and self.include_keyword.lower() not in entry_name.lower():
            return False
        
        # Filter 9: Modified in last 24 hours
        if self.modified_last_24h:
            try:
                mtime = os.path.getmtime(entry_path)
                if (time.time() - mtime) > 86400:
                    return False
            except:
                return False
        
        # Filter 10: Modified over 24 hours ago
        if self.modified_over_24h:
            try:
                mtime = os.path.getmtime(entry_path)
                if (time.time() - mtime) <= 86400:
                    return False
            except:
                return False
        
        return True

# ============================================================================
# FILTER SETUP FUNCTION
# ============================================================================

def setup_filters():
    
    filter_choice = input("Do you want to apply any filters? (yes or no): ").lower()
    
    if filter_choice != "yes":
        return None
    
    print("\nAvailable filters:")
    print("1: Only files")
    print("2: Only directories")
    print("3: Only JAR files")
    print("4: Only JSON files")
    print("5: Files smaller than 1 MB")
    print("6: Files larger than 1 MB")
    print("7: Exclude files with keyword")
    print("8: Include only files with keyword")
    print("9: Modified in last 24 hours")
    print("10: Modified over 24 hours ago")
    print("11: Show directory tree (special display mode)")
    print("\nTo select multiple filters, separate with commas (e.g., 1,3,8)")
    
    filter_input = input("Enter filter numbers (1-11): ")
    filter_list = [f.strip() for f in filter_input.split(",")]
    
    criteria = FilterCriteria()
    
    for f in filter_list:
        if f == "1":
            criteria.only_files = True
            print("✓ Filter: Only files")
        elif f == "2":
            criteria.only_dirs = True
            print("✓ Filter: Only directories")
        elif f == "3":
            criteria.only_jar = True
            print("✓ Filter: Only JAR files")
        elif f == "4":
            criteria.only_json = True
            print("✓ Filter: Only JSON files")
        elif f == "5":
            criteria.size_less_than_1mb = True
            print("✓ Filter: Files < 1 MB")
        elif f == "6":
            criteria.size_more_than_1mb = True
            print("✓ Filter: Files > 1 MB")
        elif f == "7":
            keyword = input("Enter keyword to EXCLUDE: ")
            criteria.exclude_keyword = keyword
            print(f"✓ Filter: Exclude '{keyword}'")
        elif f == "8":
            keyword = input("Enter keyword to INCLUDE: ")
            criteria.include_keyword = keyword
            print(f"✓ Filter: Include '{keyword}'")
        elif f == "9":
            criteria.modified_last_24h = True
            print("✓ Filter: Modified < 24h ago")
        elif f == "10":
            criteria.modified_over_24h = True
            print("✓ Filter: Modified > 24h ago")
        elif f == "11":
            criteria.show_tree = True
            print("✓ Special mode: Directory tree")
    
    return criteria

# ============================================================================
# DIRECTORY TREE DISPLAY
# ============================================================================

def show_directory_tree(path, indent=0, criteria=None):
    try:
        entries = os.listdir(path)
        for entry in entries:
            full_path = os.path.join(path, entry)
            is_dir = os.path.isdir(full_path)
            
            # Apply filters
            if criteria and not criteria.should_include(entry, full_path, is_dir):
                continue
            
            prefix = "  " * indent + "|-- "
            
            if is_dir:
                print(prefix + entry + "/")
                show_directory_tree(full_path, indent + 1, criteria)
            else:
                try:
                    size = os.path.getsize(full_path)
                    print(prefix + entry + f" ({size:,} bytes)")
                except:
                    print(prefix + entry)
    except PermissionError:
        print("  " * indent + "[Permission Denied]")
    except Exception as e:
        print(f"  " * indent + f"[Error: {e}]")

# ============================================================================
# COLLECT FILES WITH FILTERS
# ============================================================================

def collect_files(path, criteria=None):
    """Collect files from directory with filters applied DURING collection"""
    
    if not os.path.exists(path):
        print(f"Error: Path '{path}' does not exist.")
        return None
    
    if os.path.isfile(path):
        print("This is just a file. Skipping filter process...")
        print(f"File: {os.path.basename(path)}")
        try:
            size = os.path.getsize(path)
            print(f"Size: {size:,} bytes")
            print(f"Location: {os.path.abspath(path)}")
        except:
            pass
        return None
    
    # Special case: Tree display mode
    if criteria and criteria.show_tree:
        print("\n" + "="*60)
        print(f"DIRECTORY TREE: {path}")
        print("="*60)
        show_directory_tree(path, criteria=criteria)
        print("="*60 + "\n")
        return []  # Return empty list since we just displayed
    
    # Regular collection with filters
    data = []
    
    try:
        entries = os.listdir(path)
        
        for entry in entries:
            full_path = os.path.join(path, entry)
            is_dir = os.path.isdir(full_path)
            
            # Apply filters during collection
            if criteria and not criteria.should_include(entry, full_path, is_dir):
                continue
            
            # Calculate size
            if is_dir:
                size_str = "0 bytes"
            else:
                try:
                    size_bytes = os.path.getsize(full_path)
                    size_kb = size_bytes / 1024
                    if size_kb < 1024:
                        size_str = f"{size_kb:.2f} KB"
                    else:
                        size_mb = size_kb / 1024
                        size_str = f"{size_mb:.2f} MB"
                except:
                    size_str = "Unknown"
            
            file_data = {
                "Name": entry,
                "Type": "Directory" if is_dir else "File",
                "Size": size_str
            }
            
            data.append(file_data)
        
        print(f"\n✓ Collected {len(data)} item(s) matching filters")
        return data
        
    except PermissionError:
        print(f"Error: Permission denied accessing '{path}'")
        return None
    except Exception as e:
        print(f"Error collecting files: {e}")
        return None

# ============================================================================
# CHOICE 1: COLLECT AND STORE FILES
# ============================================================================

def choice_1(criteria):
    """Get files from directory and store in JSON"""
    
    path = input("\nEnter directory path: ")
    
    # Collect files with filters applied
    data = collect_files(path, criteria)
    
    if data is None:
        return
    
    if len(data) == 0:
        print("No files collected (filters may have excluded everything).")
        return
    
    # Ask about JSON file storage  
    create_json = input("\nCreate JSON file to store data? (yes/no): ").lower()
    if create_json == "yes":
        json_name = "dataStore.json"
        print("Do not include .json extension in the name")
        name = input("What would you like to name your JSON file? (Press Enter for 'dataStore'): ").strip()
        
        if name == "":
            json_name = "dataStore.json"
        else:
            # Remove any dots and .json extension if user included them
            name = name.replace(".json", "")  # Remove .json if present
            name = name.replace(".", "")       # Remove any other dots
            json_name = name + ".json"
        print(f"File will be named: {json_name}")
        
        # Location handling
        location = input("Where to store JSON? (Press Enter to store in program's Data_Store folder): ").strip()
        
        if location == "":
            # Store in Data_Store folder in same directory as script
            script_dir = os.path.dirname(os.path.abspath(__file__))
            data_store_dir = os.path.join(script_dir, "Data_Store")
            
            # Create Data_Store folder if it doesn't exist
            os.makedirs(data_store_dir, exist_ok=True)
            
            json_path = os.path.join(data_store_dir, json_name)
            print(f"✓ Using default location: {json_path}")
            
        elif os.path.isdir(location):
            json_path = os.path.join(location, json_name)
            print(f"✓ Saving to: {json_path}")
            
        else:
            print("⚠️  Invalid directory. Using program's Data_Store folder instead.")
            script_dir = os.path.dirname(os.path.abspath(__file__))
            data_store_dir = os.path.join(script_dir, "Data_Store")
            os.makedirs(data_store_dir, exist_ok=True)
            json_path = os.path.join(data_store_dir, json_name)
            print(f"✓ Fallback location: {json_path}")
            
    else:
        json_path = input("Enter full path for JSON file (include .json): ").strip()

    
    # Choose storage format
    print("\nStorage options:")
    print("1: Full data (Name, Type, Size)")
    print("2: Names only")
    store_type = input("Choose (1 or 2): ")
    
    if store_type == "2":
        data = [{"Name": item["Name"]} for item in data]
    
    # Save to JSON
    try:
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        print(f"\n✓ Data saved to: {json_path}")
    except Exception as e:
        print(f"Error saving JSON: {e}")

# ============================================================================
# CHOICE 2: SEARCH FOR SPECIFIC FILE
# ============================================================================

def choice_2(criteria):
    """Search for a specific file in directory tree"""
    
    path = input("\nEnter directory path to search: ")
    search_term = input("Enter filename to search for: ").lower()
    
    print(f"\nSearching for '{search_term}' in '{path}'...")
    print("-" * 60)
    
    found_count = 0
    
    for root, dirs, files in os.walk(path):
        for file in files:
            # Apply search match
            if search_term in file.lower():
                # Apply filters if any
                full_path = os.path.join(root, file)
                
                if criteria and not criteria.should_include(file, full_path, False):
                    continue
                
                found_count += 1
                print(f"\n[{found_count}] Found: {file}")
                print(f"    Path: {full_path}")
                try:
                    size = os.path.getsize(full_path)
                    print(f"    Size: {size:,} bytes")
                except:
                    pass
    
    print("-" * 60)
    if found_count == 0:
        print(f"No files matching '{search_term}' found.")
    else:
        print(f"✓ Found {found_count} file(s) matching '{search_term}'")

# ============================================================================
# CHOICE 3: MOVE FILE/DIRECTORY
# ============================================================================

def choice_3(criteria):
    """Move file or directory to new location"""
    
    source = input("\nEnter path of file/directory to move: ")
    
    if not os.path.exists(source):
        print("Error: Source path does not exist.")
        return
    
    destination = input("Enter destination path: ")
    
    # Safety check for directories
    if os.path.isdir(source):
        confirm = input("Moving a directory. Continue? (yes/no): ").lower()
        if confirm != "yes":
            print("Move cancelled.")
            return
    
    try:
        shutil.move(source, destination)
        print(f"✓ Moved '{source}' to '{destination}'")
    except Exception as e:
        print(f"Error moving: {e}")

# ============================================================================
# CHOICE 4: DELETE FILES/DIRECTORY
# ============================================================================

def choice_4(criteria):
    """Delete file or directory with filters"""
    
    if COLORAMA_AVAILABLE:
        print(Fore.RED + Style.BRIGHT + "\n⚠️  WARNING: DELETION IS PERMANENT!" + Style.RESET_ALL)
        print(Fore.YELLOW + "Proceed with caution." + Style.RESET_ALL)
    else:
        print("\n⚠️  WARNING: DELETION IS PERMANENT!")
    
    target = input("\nEnter path to delete: ")
    
    if not os.path.exists(target):
        print(f"Error: Path '{target}' does not exist.")
        return
    
    # If it's a file, just delete it
    if os.path.isfile(target):
        confirm = input(f"Delete '{target}'? (yes/no): ").lower()
        if confirm == "yes":
            try:
                os.remove(target)
                print(f"✓ Deleted: {target}")
            except Exception as e:
                print(f"Error deleting: {e}")
        return
    
    # If it's a directory
    if os.path.isdir(target):
        # If filters are active, delete only matching files
        if criteria:
            print("\nFilters active - will delete only matching files in directory.")
            data = collect_files(target, criteria)
            
            if not data or len(data) == 0:
                print("No files match filters. Nothing to delete.")
                return
            
            print(f"\nFiles to delete ({len(data)}):")
            for item in data:
                print(f"  - {item['Name']}")
            
            confirm = input(f"\nDelete all {len(data)} file(s)? (yes/no): ").lower()
            if confirm == "yes":
                deleted = 0
                for item in data:
                    file_path = os.path.join(target, item["Name"])
                    try:
                        if os.path.isfile(file_path):
                            os.remove(file_path)
                            deleted += 1
                            print(f"  ✓ Deleted: {item['Name']}")
                    except Exception as e:
                        print(f"  ✗ Error deleting {item['Name']}: {e}")
                print(f"\n✓ Deleted {deleted}/{len(data)} file(s)")
        else:
            # No filters - delete entire directory
            confirm = input(f"Delete ENTIRE directory '{target}' and all contents? (yes/no): ").lower()
            if confirm == "yes":
                try:
                    shutil.rmtree(target)
                    print(f"✓ Deleted: {target}")
                except Exception as e:
                    print(f"Error deleting: {e}")

# ============================================================================
# MAIN PROGRAM
# ============================================================================

def main():
    print("="*60)
    print("Welcome to ArborAI (Version 2)")
    print("="*60)
    
    while True:
        print("\n" + "="*60)
        print("MENU:")
        print("  1 - Collect files from directory and save to JSON")
        print("  2 - Search for specific file")
        print("  3 - Move file/directory")
        print("  4 - Delete file/directory")
        print("  exit - Exit program")
        print("="*60)
        
        choice = input("\nEnter choice (1-4 or 'exit'): ").strip().lower()
        
        if choice == "exit":
            print("\nGoodbye! 👋")
            sys.exit(0)
        
        # Setup filters
        print("\n" + "-"*60)
        criteria = setup_filters()
        print("-"*60)
        
        # Execute choice
        if choice == "1":
            choice_1(criteria)
        elif choice == "2":
            choice_2(criteria)
        elif choice == "3":
            choice_3(criteria)
        elif choice == "4":
            choice_4(criteria)
        else:
            print("Invalid choice. Please enter 1, 2, 3, 4, or 'exit'.")

if __name__ == "__main__":
    main()

def run_file_module():
    main()
